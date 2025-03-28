{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
