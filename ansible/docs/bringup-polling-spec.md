# Bringup Polling Specification (v3)

## Problem Statement

The VCF Installer bringup has two long-running API operations that need visible polling:

1. **Validation** — 10-60 minutes
2. **Bringup** — 3-4 hours

Ansible cannot stream subprocess stdout (`command`/`shell` buffer all output). The `until/retries` mechanism shows no detail on intermediate retries. The only way to show output per iteration within Ansible is `include_tasks` in a `loop` with `debug` tasks.

## Critical Design Constraints

| Constraint | Detail | Mitigation |
|-----------|--------|------------|
| Account lockout | VCF Installer locks accounts after repeated auth failures | Authenticate once, reuse token |
| Token expiry | Access tokens valid 1 hour; bringup runs 4 hours | Refresh every 50 minutes during bringup, fall back to full re-auth if refresh fails |
| Multi-Python on Mac | Ansible modules use brew Python 3.14; command tasks use system Python 3.9 | Use `ansible.builtin.uri` for ALL API calls — runs inside Ansible process, no external Python |
| `uri` SOCKS support | `uri` needs PySocks in brew Python 3.14 for SOCKS proxy | Installed via `fix_localhost_sdk.sh`; token request is the implicit verification |
| No live stdout | `command`/`shell` modules buffer stdout until exit | Use `include_tasks` loop with `debug` for immediate output |

## Token Lifecycle

```
POST /v1/tokens (1 request)
  │
  ├─ VALIDATION POLLING (≤1 hour, token valid)
  │   └─ GET /v1/sddcs/validations/{id} — reuses same token
  │
  POST /v1/tokens (1 request — fresh token for bringup phase)
  │
  ├─ BRINGUP POLLING (≤4 hours)
  │   ├─ GET /v1/sddcs/{id} — reuses token
  │   └─ Every 50 iterations (~50 min):
  │       ├─ PATCH /v1/tokens/access-token/refresh
  │       └─ If refresh fails: POST /v1/tokens (full re-auth)
  │
  Total auth requests: 2 initial + ~4 refreshes = ~6 over entire process
```

## Polling Loop Mechanism

### How `include_tasks` with `loop` and `when` works

```yaml
- name: Poll validation
  ansible.builtin.include_tasks: poll_validation.yml
  loop: "{{ range(360) | list }}"
  loop_control:
    loop_var: poll_iteration
  when: not (_poll_complete | default(false))
```

Execution flow:
1. Ansible evaluates `when` condition for iteration 0 → `_poll_complete` is false → includes `poll_validation.yml`
2. Inside `poll_validation.yml`: `uri` call, `debug` output, `set_fact`, `pause`
3. If validation still in progress: `_poll_complete` remains false → next iteration
4. If validation complete: `set_fact` sets `_poll_complete: true`
5. Ansible evaluates `when` for iteration N+1 → `_poll_complete` is true → skips include entirely
6. All remaining iterations: one "skipping" line each, no tasks executed, no pause — completes in <1 second

**Suppressing skip output**: Add `display_skipped_hosts = false` to `ansible.cfg` so remaining iterations are silent.

## File Structure

```
ansible/roles/vcf_bringup/tasks/
  main.yml              ← orchestration: auth, start, poll, result handling
  poll_validation.yml   ← single validation poll iteration (5 tasks)
  poll_bringup.yml      ← single bringup poll iteration (6 tasks)
```

## poll_validation.yml — Detailed

```yaml
---
# Single validation poll iteration
# Required vars: vcf_bringup_hostname, _vcf_token, _validation_id
# Sets: _poll_complete, _poll_final

- name: "Poll validation [{{ poll_iteration }}]"
  ansible.builtin.uri:
    url: "https://{{ vcf_bringup_hostname }}/v1/sddcs/validations/{{ _validation_id }}"
    method: GET
    validate_certs: false
    headers:
      Authorization: "Bearer {{ _vcf_token }}"
    status_code: [200]
  register: _poll_response
```

**What this returns**: `_poll_response.json` is a dict:
```json
{
  "id": "abc-123",
  "executionStatus": "IN_PROGRESS",    ← or "COMPLETED"
  "resultStatus": "",                   ← or "SUCCEEDED" / "FAILED"
  "validationChecks": [
    {"description": "JSON Spec Validation", "resultStatus": "SUCCEEDED"},
    {"description": "ESXi Host Readiness", "resultStatus": "IN_PROGRESS"},
    {"description": "vSAN Availability", "resultStatus": "NOT_STARTED",
     "errorResponse": {"errorCode": "...", "message": "..."}}
  ]
}
```

**Why `uri` not `vcf_cloud_builder` module**: `uri` reuses the token passed in the header. The module would create a new `CloudBuilder` instance, calling `POST /v1/tokens` on every iteration — 360 auth requests, risking account lockout.

```yaml
- name: "Validation [{{ poll_iteration }}] ({{ poll_iteration * 10 }}s): {{ _poll_response.json.executionStatus | default('UNKNOWN') }} — {{ _poll_response.json.validationChecks | default([]) | selectattr('resultStatus', 'equalto', 'SUCCEEDED') | list | length }}/{{ _poll_response.json.validationChecks | default([]) | length }} passed"
  ansible.builtin.debug:
    msg: >-
      {{ _poll_response.json.executionStatus | default('UNKNOWN') }}
      {% if _poll_response.json.resultStatus | default('') %}
      ({{ _poll_response.json.resultStatus }})
      {% endif %}
      — {{ _poll_response.json.validationChecks | default([]) | selectattr('resultStatus', 'equalto', 'SUCCEEDED') | list | length }}/{{ _poll_response.json.validationChecks | default([]) | length }} passed,
      {{ _poll_response.json.validationChecks | default([]) | selectattr('resultStatus', 'equalto', 'FAILED') | list | length }} failed
```

**What the operator sees** — the task name itself shows the status:
```
TASK [Validation [3] (30s): IN_PROGRESS — 5/12 passed] *******
ok: [localhost] => {
    "msg": "IN_PROGRESS — 5/12 passed, 0 failed"
}
```

The elapsed time (`30s`) is calculated from `poll_iteration * 10` (10-second delay per iteration).

```yaml
- name: Set completion state
  ansible.builtin.set_fact:
    _poll_complete: "{{ _poll_response.json.executionStatus | default('') == 'COMPLETED' }}"
    _poll_final: "{{ _poll_response.json }}"
```

**Why this is one task not two**: Combines the status parsing and completion check. `_poll_complete` is always set — to `true` or `false`. `_poll_final` always holds the latest response, so the caller always has the most recent data even if it hasn't completed yet.

```yaml
- name: Wait 10s before next poll
  ansible.builtin.pause:
    seconds: 10
  when: not (_poll_complete | bool)
```

**Skipped when complete**: No unnecessary delay after the final poll.

### Terminal output per iteration (5 lines):

```
TASK [Poll validation [3]] *******
ok: [localhost]

TASK [Validation [3] (30s): IN_PROGRESS — 5/12 passed] *******
ok: [localhost] => { "msg": "IN_PROGRESS — 5/12 passed, 0 failed" }

TASK [Set completion state] *******
ok: [localhost]

TASK [Wait 10s before next poll] *******
Pausing for 10 seconds
```

## poll_bringup.yml — Detailed

```yaml
---
# Single bringup poll iteration
# Required vars: vcf_bringup_hostname, vcf_bringup_username, vcf_bringup_password
#                _vcf_token, _vcf_refresh_token, _bringup_id
# Sets: _poll_complete, _poll_final, _vcf_token (on refresh)

- name: Refresh token (every 50 iterations)
  when: poll_iteration > 0 and poll_iteration % 50 == 0
  block:
    - name: "Refresh token [{{ poll_iteration }}]"
      ansible.builtin.uri:
        url: "https://{{ vcf_bringup_hostname }}/v1/tokens/access-token/refresh"
        method: PATCH
        validate_certs: false
        headers:
          Content-Type: text/plain
          Accept: application/json
        body: '"{{ _vcf_refresh_token }}"'
        return_content: true
        status_code: [200]
      register: _refresh_response
      failed_when: false

    - name: Update token from refresh
      ansible.builtin.set_fact:
        _vcf_token: "{{ _refresh_response.content | trim | regex_replace('^\"|\"$', '') }}"
      when: _refresh_response.status == 200

    - name: Re-authenticate if refresh failed
      when: _refresh_response.status != 200
      block:
        - name: Full re-authentication
          ansible.builtin.uri:
            url: "https://{{ vcf_bringup_hostname }}/v1/tokens"
            method: POST
            validate_certs: false
            body_format: json
            body:
              username: "{{ vcf_bringup_username }}"
              password: "{{ vcf_bringup_password }}"
            status_code: [200]
          register: _reauth_response

        - name: Update token from re-auth
          ansible.builtin.set_fact:
            _vcf_token: "{{ _reauth_response.json.accessToken }}"
            _vcf_refresh_token: "{{ _reauth_response.json.refreshToken.id }}"
```

**Token refresh details**:
- The refresh endpoint `PATCH /v1/tokens/access-token/refresh` takes the refresh token UUID as a plain text body
- Response is a new JWT access token as a string (not JSON object)
- `return_content: true` captures the response body; `regex_replace` strips any surrounding quotes
- If refresh fails (expired refresh token, 404), falls back to full `POST /v1/tokens` re-authentication
- This re-auth is at most once every 50 minutes — no lockout risk

```yaml
- name: "Poll bringup [{{ poll_iteration }}] ({{ poll_iteration * 60 // 60 }}m)"
  ansible.builtin.uri:
    url: "https://{{ vcf_bringup_hostname }}/v1/sddcs/{{ _bringup_id }}"
    method: GET
    validate_certs: false
    headers:
      Authorization: "Bearer {{ _vcf_token }}"
    status_code: [200]
  register: _poll_response

- name: "Bringup [{{ poll_iteration }}] ({{ poll_iteration }}m): {{ _poll_response.json.status | default('UNKNOWN') }}"
  ansible.builtin.debug:
    msg: "{{ _poll_response.json.status | default('UNKNOWN') }}"

- name: Set completion state
  ansible.builtin.set_fact:
    _poll_complete: "{{ _poll_response.json.status | default('') in ['COMPLETED_WITH_SUCCESS', 'COMPLETED_WITH_FAILURE'] }}"
    _poll_final: "{{ _poll_response.json }}"

- name: Wait 60s before next poll
  ansible.builtin.pause:
    seconds: 60
  when: not (_poll_complete | bool)
```

## main.yml — Orchestration

```yaml
# --- Authenticate once ---

- name: Get VCF Installer API token
  ansible.builtin.uri:
    url: "https://{{ vcf_bringup_hostname }}/v1/tokens"
    method: POST
    validate_certs: false
    body_format: json
    body:
      username: "{{ vcf_bringup_username }}"
      password: "{{ vcf_bringup_password }}"
    status_code: [200]
  register: _token_response
  no_log: true

- name: Set token facts
  ansible.builtin.set_fact:
    _vcf_token: "{{ _token_response.json.accessToken }}"
    _vcf_refresh_token: "{{ _token_response.json.refreshToken.id }}"
  no_log: true

# --- Start and poll validation ---

- name: Start SDDC validation
  ansible.builtin.uri:
    url: "https://{{ vcf_bringup_hostname }}/v1/sddcs/validations"
    method: POST
    validate_certs: false
    body_format: json
    body: "{{ vcf_bringup_spec }}"
    headers:
      Authorization: "Bearer {{ _vcf_token }}"
    status_code: [200, 202]
  register: _validation_start

- name: Set validation ID
  ansible.builtin.set_fact:
    _validation_id: "{{ _validation_start.json.id }}"

- name: Display validation ID
  ansible.builtin.debug:
    msg: "Validation started: {{ _validation_id }}"

- name: Reset poll state
  ansible.builtin.set_fact:
    _poll_complete: false
    _poll_final: {}

- name: Poll validation
  ansible.builtin.include_tasks: poll_validation.yml
  loop: "{{ range(360) | list }}"
  loop_control:
    loop_var: poll_iteration
    label: "poll {{ poll_iteration }}"
  when: not (_poll_complete | default(false) | bool)

- name: Fail if validation timed out
  ansible.builtin.fail:
    msg: "Validation timed out after 1 hour."
  when: not (_poll_complete | bool)

# --- Display validation results ---

- name: Display all validation checks
  ansible.builtin.debug:
    msg: "{{ ('✓' if item.resultStatus == 'SUCCEEDED' else '✗') }} [{{ item.resultStatus }}] {{ item.description | default('Unknown') }}"
  loop: "{{ _poll_final.validationChecks | default([]) }}"
  loop_control:
    label: "{{ item.description | default('check') }}"

- name: Fail if unexpected validation errors
  vars:
    _failed_checks: "{{ _poll_final.validationChecks | default([]) | selectattr('resultStatus', 'equalto', 'FAILED') | list }}"
    _known_safe_codes:
      - VSAN_ESA_HOST_NOT_HCL_COMPATIBLE
      - NO_VSAN_ESA_CERTIFIED_DISKS
      - EXISTING_SDDC_VALIDATION_WARNING
    _unexpected: "{{ _failed_checks | map(attribute='errorResponse') | map(attribute='errorCode', default='') | reject('in', _known_safe_codes) | list }}"
  ansible.builtin.fail:
    msg: >-
      Validation failed with {{ _unexpected | length }} unexpected error(s).
      Failed checks: {{ _failed_checks | map(attribute='description') | list }}
  when:
    - _poll_final.resultStatus | default('') != 'SUCCEEDED'
    - _unexpected | length > 0

# --- Start and poll bringup ---

- name: Get fresh token for bringup
  ansible.builtin.uri:
    url: "https://{{ vcf_bringup_hostname }}/v1/tokens"
    method: POST
    validate_certs: false
    body_format: json
    body:
      username: "{{ vcf_bringup_username }}"
      password: "{{ vcf_bringup_password }}"
    status_code: [200]
  register: _token_response
  no_log: true

- name: Set fresh token facts
  ansible.builtin.set_fact:
    _vcf_token: "{{ _token_response.json.accessToken }}"
    _vcf_refresh_token: "{{ _token_response.json.refreshToken.id }}"
  no_log: true

- name: Start SDDC bringup
  ansible.builtin.uri:
    url: "https://{{ vcf_bringup_hostname }}/v1/sddcs"
    method: POST
    validate_certs: false
    body_format: json
    body: "{{ vcf_bringup_spec }}"
    headers:
      Authorization: "Bearer {{ _vcf_token }}"
    status_code: [200, 202]
  register: _bringup_start

- name: Set bringup ID
  ansible.builtin.set_fact:
    _bringup_id: "{{ _bringup_start.json.id }}"

- name: Display bringup ID
  ansible.builtin.debug:
    msg: "Bringup started: {{ _bringup_id }}. Monitor at https://{{ vcf_bringup_hostname }}"

- name: Reset poll state
  ansible.builtin.set_fact:
    _poll_complete: false
    _poll_final: {}

- name: Poll bringup
  ansible.builtin.include_tasks: poll_bringup.yml
  loop: "{{ range(240) | list }}"
  loop_control:
    loop_var: poll_iteration
    label: "poll {{ poll_iteration }}"
  when: not (_poll_complete | default(false) | bool)

- name: Fail if bringup timed out
  ansible.builtin.fail:
    msg: "Bringup timed out after 4 hours."
  when: not (_poll_complete | bool)

- name: Fail if bringup failed
  ansible.builtin.fail:
    msg: "SDDC bringup failed: {{ _poll_final.status | default('UNKNOWN') }}"
  when: "'FAILURE' in (_poll_final.status | default(''))"

- name: Bringup complete
  ansible.builtin.debug:
    msg: "SDDC bringup {{ _poll_final.status }}"
```

## ansible.cfg Change

```ini
[defaults]
display_skipped_hosts = false
```

Suppresses the "skipping: [localhost]" lines after polling completes and remaining loop iterations are skipped.

## Verification Plan

| Step | How to verify | Expected result |
|------|--------------|-----------------|
| PySocks in brew Python | `fix_localhost_sdk.sh` succeeded | No SOCKS errors |
| Token endpoint | Token request returns 200 with `accessToken` | First `uri` task succeeds |
| SOCKS proxy for `uri` | Token request succeeds through proxy | Connection established |
| Validation start | `POST /v1/sddcs/validations` returns 200/202 with `id` | Validation ID displayed |
| Poll output visible | Each iteration shows task name with status | `TASK [Validation [3] (30s): IN_PROGRESS — 5/12 passed]` |
| Early exit on completion | After COMPLETED, remaining iterations skip silently | No pause, no API calls |
| Validation failure display | Failed checks shown with description and error code | Clear error output |
| Known-safe bypass | HCL warnings don't fail the playbook | Continues to bringup |
| Token refresh | At iteration 50 of bringup, token refreshes | No 401 errors |
| Refresh fallback | If refresh fails, full re-auth succeeds | Bringup continues |
| Bringup completion | COMPLETED_WITH_SUCCESS stops polling | Success message |
| Bringup failure | COMPLETED_WITH_FAILURE stops polling and fails playbook | Clear error |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Account lockout | Eliminated | High | 2 auth requests total, ~4 refreshes |
| Token expiry during bringup | Expected | Medium | Proactive refresh + re-auth fallback |
| SOCKS tunnel drops | Low | High | `ssh -f -N` persists, caffeinate active |
| `uri` SOCKS failure | Low (if fix script ran) | High | Token request is implicit verification |
| VCF Installer unreachable | Low | Medium | `uri` task fails, playbook stops with clear error |
| Queued validations from previous runs | Medium | Low | New validation gets its own ID, polls correctly |
