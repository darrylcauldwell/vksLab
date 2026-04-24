{ config, pkgs, lib, ... }:

{
  # System basics
  system.stateVersion = "24.11";
  time.timeZone = "UTC";

  # VMware guest support
  virtualisation.vmware.guest.enable = true;

  # Networking
  networking = {
    hostName = "nixos-vsphere";
    firewall = {
      enable = true;
      allowedTCPPorts = [ 22 ];
    };
  };

  # Enable SSH
  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "prohibit-password";
      PasswordAuthentication = false;
    };
  };

  # Base packages
  environment.systemPackages = with pkgs; [
    vim
    git
    curl
    htop
  ];

  # Default user
  users.users.admin = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];
    openssh.authorizedKeys.keys = [
      # Add your SSH public key here
    ];
  };

  # Allow sudo without password for wheel group
  security.sudo.wheelNeedsPassword = false;

  # Enable nix flakes
  nix.settings.experimental-features = [ "nix-command" "flakes" ];
}
