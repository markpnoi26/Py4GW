import os
import configparser
import ast


# region IniHandlerV2
class IniHandlerV2:
    def __init__(self, filename: str, generate_new: bool = False):
        self.base_filename = filename
        self.local_filename = filename.replace(".ini", ".local.ini")

        self.base_config = configparser.ConfigParser()
        self.local_config = configparser.ConfigParser()
        self.config = configparser.ConfigParser()

        # NEW: force rebuild local.ini if requested
        if generate_new and os.path.exists(self.local_filename):
            os.remove(self.local_filename)

        self.reload()

    # -------------------------------------------------------------------
    # Helper: attempt to infer type to validate local.ini values
    # -------------------------------------------------------------------
    def _typed(self, base_value: str, local_value: str):
        """Force local_value to match base_value’s type, or return base_value."""
        try:
            # Try int
            if isinstance(ast.literal_eval(base_value), int):
                return str(int(local_value))
        except Exception:
            pass
        try:
            # Try float
            if isinstance(ast.literal_eval(base_value), float):
                return str(float(local_value))
        except Exception:
            pass
        try:
            # Try bool
            if base_value.lower() in ["true", "false"]:
                lv = local_value.lower()
                if lv in ["true", "1", "yes"]:
                    return "true"
                if lv in ["false", "0", "no"]:
                    return "false"
        except Exception:
            pass

        # Fallback: return local_value if it’s a valid string
        return local_value

    # -------------------------------------------------------------------
    # Core: reload + auto-repair local.ini to match schema of base.ini
    # -------------------------------------------------------------------
    def reload(self) -> configparser.ConfigParser:
        # Read files
        self.base_config.read(self.base_filename)
        self.local_config.read(self.local_filename)

        # If local.ini missing → copy base.ini
        if not os.path.exists(self.local_filename):
            with open(self.local_filename, "w") as f:
                self.base_config.write(f)
            self.local_config.read(self.local_filename)

        # If local.ini has 0 sections → treat as empty/corrupt
        if len(self.local_config.sections()) == 0:
            with open(self.local_filename, "w") as f:
                self.base_config.write(f)
            self.local_config.read(self.local_filename)

        # -------------------------------------------------------------------
        # STEP 1 — Remove sections not in base.ini
        # -------------------------------------------------------------------
        for section in list(self.local_config.sections()):
            if not self.base_config.has_section(section):
                self.local_config.remove_section(section)

        # -------------------------------------------------------------------
        # STEP 2 — Fix keys inside each section
        # -------------------------------------------------------------------
        for section in self.base_config.sections():

            # Ensure section exists
            if not self.local_config.has_section(section):
                self.local_config.add_section(section)

            # Remove extra keys in local.ini
            for key in list(self.local_config[section].keys()):
                if not self.base_config.has_option(section, key):
                    self.local_config.remove_option(section, key)

            # Add or validate keys
            for key, base_value in self.base_config.items(section):

                # If key missing → add from base
                if not self.local_config.has_option(section, key):
                    self.local_config.set(section, key, base_value)
                    continue

                # Validate type
                local_value = self.local_config.get(section, key)
                fixed_value = self._typed(base_value, local_value)

                # If type mismatch or invalid → restore base value
                if fixed_value != local_value:
                    self.local_config.set(section, key, base_value)

        # Save repaired local.ini
        with open(self.local_filename, "w") as f:
            self.local_config.write(f)

        # -------------------------------------------------------------------
        # Build final merged config (base + local override)
        # -------------------------------------------------------------------
        merged = configparser.ConfigParser()

        for section in self.base_config.sections():
            merged.add_section(section)
            for k, v in self.base_config.items(section):
                merged.set(section, k, v)

        for section in self.local_config.sections():
            for k, v in self.local_config.items(section):
                merged.set(section, k, v)

        self.config = merged
        return self.config

    def save(self, config: configparser.ConfigParser):
        if not config:
            config = self.config
        with open(self.local_filename, "w") as f:
            config.write(f)

    # -------------------------------------------------------------------
    def write_key(self, section: str, key: str, value) -> None:
        """Always write to local.ini, then reload to enforce type/schema rules."""
        self.local_config.read(self.local_filename)

        if not self.local_config.has_section(section):
            self.local_config.add_section(section)

        self.local_config.set(section, key, str(value))

        with open(self.local_filename, "w") as f:
            self.local_config.write(f)

        self.reload()

    # ---------------------------------------------------------------
    # Read Helpers
    # ---------------------------------------------------------------
    def read_key(self, section, key, default=""):
        try:
            return self.config.get(section, key)
        except Exception:
            return default

    def read_int(self, section, key, default=0):
        try:
            return self.config.getint(section, key)
        except Exception:
            return default

    def read_float(self, section, key, default=0.0):
        try:
            return self.config.getfloat(section, key)
        except Exception:
            return default

    def read_bool(self, section, key, default=False):
        try:
            return self.config.getboolean(section, key)
        except Exception:
            return default

    # ----------------------------
    # Utility Methods
    # ----------------------------

    def list_sections(self) -> list:
        """
        List all sections in the INI file.
        """
        config = self.reload()
        return config.sections()

    def list_keys(self, section: str) -> dict:
        """
        List all keys and values in a section.
        """
        config = self.reload()
        if config.has_section(section):
            return dict(config.items(section))
        return {}

    def has_key(self, section: str, key: str) -> bool:
        """
        Check if a key exists in a section.
        """
        config = self.reload()
        return config.has_section(section) and config.has_option(section, key)

    def clone_section(self, source_section: str, target_section: str) -> None:
        """
        Clone all keys from one section to another.
        """
        config = self.reload()
        if config.has_section(source_section):
            if not config.has_section(target_section):
                config.add_section(target_section)
            for key, value in config.items(source_section):
                config.set(target_section, key, value)
            self.save(config)
