{
  description = "json2ansi: Python application";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-unstable";
    utils.url = "flake-utils";
  };

  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };

      python = pkgs.python3.withPackages (ps: with ps; [
        jsonschema
        jsonref
        rich
        json5
        setuptools
      ]);
      pythonPackages = python.pkgs;

      propagatedBuildInputs = [ python ];

      env = {
        PYTHON_NIX = "${python.interpreter}";
      };

    in {
      devShell = pkgs.mkShell {
        inherit env;
        packages = propagatedBuildInputs;
        shellHook = ''
        '';
      };

      packages = rec {
        json2ansi = pythonPackages.buildPythonApplication {
          inherit propagatedBuildInputs;
          pname = "json2ansi";
          version = "1.0.0";
          src = ./.;
          format = "pyproject";
        };

        default = json2ansi;
      };
    }
  );
}