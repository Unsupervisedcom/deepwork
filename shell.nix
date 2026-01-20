# Legacy nix-shell compatibility wrapper
# This file provides backward compatibility for users still using `nix-shell`.
# It imports the devShell from flake.nix, ensuring the same environment
# regardless of whether you use `nix-shell` or `nix develop`.
#
# Modern users should use:
#   nix develop       (flakes)
# or with direnv:
#   direnv allow      (automatically uses the flake)
#
# Legacy users can still use:
#   nix-shell         (uses this compatibility wrapper)

(import (
  fetchTarball {
    url = "https://github.com/edolstra/flake-compat/archive/master.tar.gz";
    sha256 = "0pf91w4f6nnlxy3z1vdz5jq9b4qqls4s7xhd0pahph8smxka91w7";
  }
) {
  src = ./.;
}).shellNix
