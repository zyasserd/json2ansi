{
  description = "A python template";
  
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    
    # in the nix global registry: `github:numtide/flake-utils`
    utils.url = "flake-utils";
  };

  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs {
        inherit system;
        # config.allowUnfree = true;
      };

      python = pkgs.python3; # change version here
      pythonPackages = python.pkgs;

      # (( build a package from PyPI ))
      # myPackage = pythonPackages.buildPythonPackage rec {
      #   pname = "<fill>";
      #   version = "<fill>";
      #   format = "wheel";
      #
      #   src = pythonPackages.fetchPypi {
      #     inherit pname version format;
      #     python = "py3";
      #     dist = "py3";
      #     sha256 = "";
      #   };
      #
      #   dependencies = with pythonPackages; [
      #
      #   ];
      #
      #   # doCheck = false;
      # };
      
    in {

      # `devShell` or `devShells.default`
      devShell = pkgs.mkShell {
        # The Nix packages provided in the environment
        # Add any you need here
        packages = [ 
          (python.withPackages (p: with p; [
            jsonschema
            jsonref
            rich
          ]))
        ];

        # Set any environment variables for your dev shell
        env = {
          # To be used by "ms-python.python" to set the correct version,
          #   combined with vscode settings in .vscode dir.
          PYTHON_NIX = "${python.interpreter}";
        };

        # Add any shell logic you want executed any time the environment is activated
        shellHook = ''
        '';
      };


      packages = rec {
        hello = pkgs.hello;
        default = hello;
      };

    }
  );

}