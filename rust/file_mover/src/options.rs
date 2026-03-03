#[derive(Debug, Clone)]
pub struct MoveOptions {
    /// Use atomic move operations
    pub atomic: bool,
    
    /// Verify file integrity after move using checksums
    pub verify_checksum: bool,
    
    /// Preserve file permissions and timestamps
    pub preserve_metadata: bool,
    
    /// Create target directories automatically
    pub create_dirs: bool,
    
    /// Overwrite existing files (currently not implemented, reserved for future use)
    pub overwrite_existing: bool,
}

impl Default for MoveOptions {
    fn default() -> Self {
        Self {
            atomic: true,
            verify_checksum: true,
            preserve_metadata: true,
            create_dirs: true,
            overwrite_existing: false,
        }
    }
}

impl MoveOptions {
    /// Creates a new MoveOptions with default settings
    pub fn new() -> Self {
        Self::default()
    }

    /// Builder method to set atomic option
    pub fn atomic(mut self, atomic: bool) -> Self {
        self.atomic = atomic;
        self
    }

    /// Builder method to set verify_checksum option
    pub fn verify_checksum(mut self, verify: bool) -> Self {
        self.verify_checksum = verify;
        self
    }

    /// Builder method to set preserve_metadata option
    pub fn preserve_metadata(mut self, preserve: bool) -> Self {
        self.preserve_metadata = preserve;
        self
    }

    /// Builder method to set create_dirs option
    pub fn create_dirs(mut self, create: bool) -> Self {
        self.create_dirs = create;
        self
    }

    /// Builder method to set overwrite_existing option
    pub fn overwrite_existing(mut self, overwrite: bool) -> Self {
        self.overwrite_existing = overwrite;
        self
    }
}
