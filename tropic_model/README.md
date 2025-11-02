This directory contains files needed to launch the "Tropic model" - [ts-tvl](https://github.com/tropicsquare/ts-tvl/) - which is used to simulate the presence of the TROPIC01 chip during tests.

The Tropic model requires:
 * (I) a keypair and a certificate it will use to communicate to the host (`tropic01_ese_*`) - these are simply copied from [example_config](https://github.com/tropicsquare/ts-tvl/tree/master/model_configs/example_config)
 * (II) a certificate chain and a keypair that will be used during Trezor's authenticity check

`ts-tvl` then uses a YAML config file to load the above keys and certificates.
 * (I) go into: `s_t_priv`, `s_t_pub` and `x509_certificate` as required by [`ts-tvl`](https://github.com/tropicsquare/ts-tvl/blob/master/model_configs/example_config/example_config.yml)
 * (II) go into: `r_ecc_keys` and `r_user_data` as required by [Trezor's authenticity check](https://github.com/trezor/trezor-firmware/blob/main/core/src/apps/management/authenticate_device.py)

The config file itself is generated using `core/tools/generate_tropic_model_config.py`.
