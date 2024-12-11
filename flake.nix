{
  description = "Flake for Pythonic bindings for irace: Iterated Racing for Automatic Algorithm Configuration";

  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
    poetry2nix.url = "github:nix-community/poetry2nix";
    poetry2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs = {
    self,
    nixpkgs,
    devenv,
    systems,
    poetry2nix,
    ...
  } @ inputs: let
    forEachSystem = nixpkgs.lib.genAttrs (import systems);

    # `irace` development version.
    irace-dev = pkgs:
      pkgs.rPackages.buildRPackage {
        name = "irace";
        src = builtins.fetchGit {
          url = "https://github.com/MLopez-Ibanez/irace";
          ref = "master";
          rev = "30c8d4702960f76b31cdf4bf82c66082ab23934b";
        };
        # Dependencies extracted from `DESCRIPTION` file in repository.
        propagatedBuildInputs = with pkgs.rPackages; [fs data_table matrixStats R6 spacefillr withr highr knitr testthat];
        # Rmpi needed to be removed until it supports openmpi >= 5.0 properly
      };
  in {
    # Necessary for `rpy2` to be installable with poetry.
    nixpkgs.overlays = [
      (self: super: {
        icuuc = self.icu;
        icui18n = self.icu;
        icudata = self.icu;
      })
    ];

    packages = forEachSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      inherit (poetry2nix.lib.mkPoetry2Nix {inherit pkgs;}) mkPoetryApplication;
    in {
      devenv-up = self.devShells.${system}.default.config.procfileScript;
      iracepy-tiny = mkPoetryApplication {
        projectDir = self;
        preferWheels = true;
        python = pkgs.python312;
        propagatedBuildInputs = [
          pkgs.R
          (irace-dev pkgs)
          pkgs.python312Packages.rpy2
        ];
      };
      default = self.packages.${system}.iracepy-tiny;
    });

    devShells =
      forEachSystem
      (system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        default = devenv.lib.mkShell {
          inherit inputs pkgs;
          modules = [
            {
              languages = {
                python = {
                  enable = true;
                  package = pkgs.python312;
                  poetry.enable = true;
                };
              };
              packages = [pkgs.R pkgs.mpi (irace-dev pkgs) pkgs.python312Packages.rpy2];
            }
          ];
        };
      });
  };
}
