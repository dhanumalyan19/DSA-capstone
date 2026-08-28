"""
gui/app_state.py
-----------------
A small shared-state object plus a simple observer/listener pattern so
the six GUI tabs can stay in sync without being tightly coupled to each
other. Whenever the Compress tab builds a new tree/encodes new data (or
the Decompress tab loads/decodes a file), it updates this object and
calls `notify()`; every registered tab's `on_state_changed()` is then
invoked so it can refresh its own display.

This keeps GUI code separate from DSA/core logic: AppState only stores
references to core objects (HuffmanNode, CompressedPackage, etc.) and
plain data -- it contains no algorithm logic itself.
"""


class AppState:
    def __init__(self):
        # ---- Compress-side state -------------------------------------
        self.source_text = ""                 # raw input text (typed or loaded)
        self.source_file_path = None          # path if loaded from a file
        self.frequencies = {}                 # symbol -> count
        self.tree_root = None                 # HuffmanNode (root)
        self.codes = {}                       # symbol -> code string
        self.build_steps = []                 # narration from tree construction
        self.package = None                   # CompressedPackage (last encode)
        self.encode_steps = []
        self.encoding_seconds = None
        self.last_saved_compressed_path = None

        # ---- Decompress-side state --------------------------------------
        self.loaded_compressed_path = None
        self.loaded_frequencies = None
        self.loaded_padding_bits = None
        self.loaded_original_symbol_count = None
        self.loaded_packed_bytes = None
        self.decoded_text = None
        self.decoding_seconds = None
        self.verification_result = None       # True / False / None

        # ---- listeners -------------------------------------------------
        self._listeners = []

    def register(self, listener):
        """Register an object with an `on_state_changed()` method."""
        self._listeners.append(listener)

    def notify(self):
        for listener in self._listeners:
            handler = getattr(listener, "on_state_changed", None)
            if callable(handler):
                handler()

    def has_tree(self):
        return self.tree_root is not None

    def reset_compress_side(self):
        self.source_text = ""
        self.source_file_path = None
        self.frequencies = {}
        self.tree_root = None
        self.codes = {}
        self.build_steps = []
        self.package = None
        self.encode_steps = []
        self.encoding_seconds = None
