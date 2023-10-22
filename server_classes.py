from dataclasses import dataclass
from typing import Any


@dataclass
class Config:
    port: int
    threads: int
    verbose: bool
    check_public_ip: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            'port': self.port,
            'threads': self.threads,
            'verbose': self.verbose,
            'check-public-ip': self.check_public_ip
        }


class Utils:
    def __init__(self, config: Config):
        self.config = config

    def verbose_print(self,
                      *values: object,
                      sep: str | None = ...,
                      end: str | None = ...,
                      invert_check: bool = False) -> None:
        if self.config.verbose != invert_check:
            print(*values, sep=sep, end=end)
