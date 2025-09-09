{
  description = "Flake for Pythonic bindings for irace: Iterated Racing for Automatic Algorithm Configuration";

  inputs = {
    nixpkgs.url = "github:cachix/devenv-nixpkgs/rolling";
    systems.url = "github:nix-systems/default";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
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
    ...
  } @ inputs: let
    forEachSystem = nixpkgs.lib.genAttrs (import systems);

    # Irace 4.2 requires matrixStats >= 1.4.1, which is not yet in devenv nixpkgs.
    matrixStats_1_5_0 = pkgs:
      pkgs.rPackages.buildRPackage {
        name = "matrixStats-1.5.0";
        pname = "matrixStats";
        version = "1.5.0";
        src = pkgs.fetchurl {
          url = "https://cran.r-project.org/src/contrib/matrixStats_1.5.0.tar.gz";
          sha256 = "sha256-EplsXz5vwgKkPhCH8Wpxt/qT1+kI9RJULH7onPldzBU=";
        };
      };

    irace_4_2_0 = pkgs:
      pkgs.rPackages.buildRPackage {
        name = "irace-4.2.0";
        pname = "irace";
        version = "4.2.0";
        src = pkgs.fetchurl {
          url = "https://cran.r-project.org/src/contrib/irace_4.2.0.tar.gz";
          sha256 = "sha256-WM/mSHFBmBp5QRVX5wkGH/r8oVo2KJpx3U5QqK/kp7E=";
        };
        # Dependencies extracted from `DESCRIPTION` file in repository.
        propagatedBuildInputs = with pkgs.rPackages; [
          fs
          data_table
          R6
          spacefillr
          withr
          highr
          knitr
          testthat
          codetools
          (matrixStats_1_5_0 pkgs)
        ];
      };
  in {
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
                  uv = {
                    enable = true;
                    sync.enable = true;
                  };
                };
              };
              packages = with pkgs; [R (irace_4_2_0 pkgs) libdeflate icu libz];
            }
          ];
        };
      });
  };
}
