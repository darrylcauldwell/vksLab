{
  description = "NixOS vSphere VM image";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    nixos-generators = {
      url = "github:nix-community/nixos-generators";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, nixos-generators, ... }: {
    packages.x86_64-linux.vsphere-image = nixos-generators.nixosGenerate {
      system = "x86_64-linux";
      format = "vmware";
      modules = [
        ./nixos/configuration.nix
      ];
    };

    packages.x86_64-linux.default = self.packages.x86_64-linux.vsphere-image;
  };
}
