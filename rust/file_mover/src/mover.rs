use std::collections::{HashMap, HashSet};
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use std::fmt::Write as FmtWrite;

use blake3::Hasher;
use parking_lot::Mutex;

use crate::models::{MoveError, MoveResult, MoveStatus};
use crate::options::MoveOptions;

const BUFFER_SIZE: usize = 65536;

/// Handles moving files with specified options and safety checks
pub struct FileMover {
    options: MoveOptions,
    collision_cache: Mutex<HashMap<PathBuf, HashSet<String>>>,
}

impl FileMover {
    /// Creates a new FileMover with the given options
    pub fn new(options: MoveOptions) -> Self {
        Self {
            options,
            collision_cache: Mutex::new(HashMap::new()),
        }
    }

    /// Creates a new FileMover with default options
    pub fn with_defaults() -> Self {
        Self::new(MoveOptions::default())
    }

    /// Moves a file to the specified destination directory
    pub fn move_file(
        &self,
        source: impl AsRef<Path>,
        destination_dir: impl AsRef<Path>,
        filename: Option<&str>,
        category: Option<String>,
        dry_run: bool,
    ) -> MoveResult {
        let source = source.as_ref();
        let destination_dir = destination_dir.as_ref();

        // Validate source file
        if let Err(error) = self.validate_source(source) {
            return MoveResult::failed(source.to_path_buf(), category, error);
        }

        // Determine target filename
        let target_filename = filename
            .map(String::from)
            .unwrap_or_else(|| {
                source
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unnamed")
                    .to_string()
            });

        // Get unique filename to avoid collisions
        let unique_filename = match self.get_unique_filename(destination_dir, &target_filename) {
            Ok(name) => name,
            Err(error) => {
                return MoveResult::failed(source.to_path_buf(), category, error);
            }
        };

        let dest = destination_dir.join(&unique_filename);

        // Skip if source and destination are the same
        if source == dest {
            log::info!("[Skipped] Moving {:?} to {:?}", source, dest);
            return MoveResult::skipped(source.to_path_buf(), dest, category);
        }

        // Skip if destination exists and overwrite is not allowed
        if dest.exists() && !self.options.overwrite_existing {
            log::info!("[Skipped] Destination {:?} already exists", dest);
            return MoveResult::skipped(source.to_path_buf(), dest, category);
        }

        // Handle dry run
        if dry_run {
            log::info!("[Dry Run] Moving {:?} to {:?}", source, dest);
            return MoveResult::dry_run(source.to_path_buf(), dest, category);
        }

        // Create destination directory if needed
        if self.options.create_dirs {
            if let Err(e) = fs::create_dir_all(destination_dir) {
                self.invalidate_cache(destination_dir);
                return MoveResult::failed(source.to_path_buf(), category, MoveError::Io(e));
            }
        }

        // Perform the move operation
        if let Err(error) = self.perform_move(source, &dest) {
            self.invalidate_cache(destination_dir);
            return MoveResult::failed(source.to_path_buf(), category, error);
        }

        // Verify the move if checksum verification is enabled
        if self.options.verify_checksum {
            if let Err(error) = self.verify_move(source, &dest) {
                self.invalidate_cache(destination_dir);
                return MoveResult::failed(source.to_path_buf(), category, error);
            }
        }

        log::debug!("Moved {:?} -> {:?}", source, dest);
        MoveResult::success(source.to_path_buf(), dest, category)
    }

    /// Validates that the source path exists and is a file
    #[inline]
    fn validate_source(&self, source: &Path) -> Result<(), MoveError> {
        if !source.exists() {
            return Err(MoveError::SourceNotFound(source.to_path_buf()));
        }

        if !source.is_file() {
            return Err(MoveError::NotAFile(source.to_path_buf()));
        }

        Ok(())
    }

    /// Performs the actual move operation based on options
    #[inline]
    fn perform_move(&self, source: &Path, dest: &Path) -> Result<(), MoveError> {
        if self.options.atomic {
            self.atomic_move(source, dest)
        } else {
            self.simple_move(source, dest)
        }
    }

    /// Performs a simple move operation
    fn simple_move(&self, source: &Path, dest: &Path) -> Result<(), MoveError> {
        fs::rename(source, dest).map_err(|e| {
            if e.kind() == io::ErrorKind::PermissionDenied {
                MoveError::PermissionDenied(format!("{:?}", source))
            } else {
                MoveError::Io(e)
            }
        })
    }

    /// Performs an atomic move operation with fallback for cross-filesystem moves
    fn atomic_move(&self, source: &Path, dest: &Path) -> Result<(), MoveError> {
        // Try simple rename first (atomic on same filesystem)
        match fs::rename(source, dest) {
            Ok(()) => {
                log::debug!("Atomic rename: {:?} -> {:?}", source, dest);
                Ok(())
            }
            Err(e) if self.is_cross_filesystem_error(&e) => {
                log::debug!("Cross-filesystem move: {:?} -> {:?}", source, dest);
                self.cross_filesystem_move(source, dest)
            }
            Err(e) => {
                if e.kind() == io::ErrorKind::PermissionDenied {
                    Err(MoveError::PermissionDenied(format!("{:?}", source)))
                } else {
                    Err(MoveError::Io(e))
                }
            }
        }
    }

    /// Checks if an error indicates a cross-filesystem operation
    #[inline]
    fn is_cross_filesystem_error(&self, error: &io::Error) -> bool {
        #[cfg(unix)]
        {
            error.raw_os_error() == Some(libc::EXDEV)
        }

        #[cfg(not(unix))]
        {
            matches!(
                error.kind(),
                io::ErrorKind::InvalidInput | io::ErrorKind::Other
            )
        }
    }

    fn cross_filesystem_move(&self, source: &Path, dest: &Path) -> Result<(), MoveError> {
        let temp_dest = dest.with_extension("tmp");
        let _guard = TempFileGuard::new(&temp_dest);

        // Use larger buffer for better throughput
        let mut buffer = vec![0u8; BUFFER_SIZE];
        
        let mut src_file = File::open(source)?;
        let mut dst_file = File::create(&temp_dest)?;

        // Manual copy with large buffer
        loop {
            let bytes_read = src_file.read(&mut buffer)?;
            if bytes_read == 0 {
                break;
            }
            use std::io::Write;
            dst_file.write_all(&buffer[..bytes_read])?;
        }

        // Ensure all data is written
        use std::io::Write;
        dst_file.flush()?;
        drop(dst_file);

        // Copy metadata if requested
        if self.options.preserve_metadata {
            self.copy_metadata(source, &temp_dest)?;
        }

        // Atomically rename temp file to final destination
        fs::rename(&temp_dest, dest)?;

        // Only delete source after successful move
        fs::remove_file(source)?;

        // Disarm the guard
        std::mem::forget(_guard);

        Ok(())
    }

    /// Copies metadata (permissions and timestamps) from source to destination
    fn copy_metadata(&self, source: &Path, dest: &Path) -> Result<(), MoveError> {
        let metadata = fs::metadata(source)?;
        let permissions = metadata.permissions();
        fs::set_permissions(dest, permissions)?;

        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            let atime = metadata.atime();
            let mtime = metadata.mtime();
            
            unsafe {
                let path_cstring = std::ffi::CString::new(dest.to_str().unwrap()).unwrap();
                let times = [
                    libc::timespec {
                        tv_sec: atime,
                        tv_nsec: 0,
                    },
                    libc::timespec {
                        tv_sec: mtime,
                        tv_nsec: 0,
                    },
                ];
                libc::utimensat(
                    libc::AT_FDCWD,
                    path_cstring.as_ptr(),
                    times.as_ptr(),
                    0,
                );
            }
        }

        Ok(())
    }

    /// Verifies that the move was successful by comparing checksums
    fn verify_move(&self, source: &Path, dest: &Path) -> Result<(), MoveError> {
        // If source no longer exists and dest does, the move was successful
        if !source.exists() && dest.exists() {
            return Ok(());
        }

        let source_hash = Self::file_checksum(source)?;
        let dest_hash = Self::file_checksum(dest)?;

        if source_hash == dest_hash {
            Ok(())
        } else {
            Err(MoveError::IntegrityCheckFailed)
        }
    }

    fn file_checksum(path: &Path) -> Result<String, MoveError> {
        let mut file = File::open(path)?;
        let mut hasher = Hasher::new();
        let mut buffer = vec![0u8; BUFFER_SIZE];

        loop {
            let bytes_read = file.read(&mut buffer)?;
            if bytes_read == 0 {
                break;
            }
            hasher.update(&buffer[..bytes_read]);
        }

        Ok(hasher.finalize().to_hex().to_string())
    }

    fn get_unique_filename(
        &self,
        directory: &Path,
        filename: &str,
    ) -> Result<String, MoveError> {
        const MAX_ATTEMPTS: usize = 10000;

        let mut cache = self.collision_cache.lock();

        if !cache.contains_key(directory) {
            let existing_files = if directory.exists() {
                fs::read_dir(directory)
                    .map(|entries| {
                        entries
                            .filter_map(|entry| entry.ok())
                            .filter(|entry| entry.path().is_file())
                            .filter_map(|entry| entry.file_name().to_str().map(String::from))
                            .collect()
                    })
                    .unwrap_or_else(|_| HashSet::new())
            } else {
                HashSet::new()
            };

            cache.insert(directory.to_path_buf(), existing_files);
        }

        let existing_files = cache.get_mut(directory).unwrap();

        // If overwrite is enabled, use the original filename without uniqueness check
        if self.options.overwrite_existing {
            return Ok(filename.to_string());
        }

        // Check if filename is already unique
        if !existing_files.contains(filename) {
            existing_files.insert(filename.to_string());
            return Ok(filename.to_string());
        }

        // Generate numbered variants
        let path = Path::new(filename);
        let stem = path.file_stem().and_then(|s| s.to_str()).unwrap_or("unnamed");
        let extension = path.extension().and_then(|e| e.to_str()).unwrap_or("");

        // Pre-allocate with estimated capacity to reduce allocations
        let estimated_capacity = stem.len() + extension.len() + 15;
        let mut new_filename = String::with_capacity(estimated_capacity);

        for count in 1..=MAX_ATTEMPTS {
            new_filename.clear();
            new_filename.push_str(stem);
            new_filename.push('(');
            
            // Use fmt::Write for efficient integer formatting
            write!(&mut new_filename, "{}", count).unwrap();
            
            new_filename.push(')');
            
            if !extension.is_empty() {
                new_filename.push('.');
                new_filename.push_str(extension);
            }

            // Check filename length (255 bytes for most filesystems)
            if new_filename.len() > 255 {
                // Truncate stem to fit within limit
                let overhead = format!("({}).{}", count, extension).len();
                let max_stem_len = 255_usize.saturating_sub(overhead);
                
                new_filename.clear();
                new_filename.push_str(&stem[..max_stem_len.min(stem.len())]);
                new_filename.push('(');
                write!(&mut new_filename, "{}", count).unwrap();
                new_filename.push(')');
                
                if !extension.is_empty() {
                    new_filename.push('.');
                    new_filename.push_str(extension);
                }
            }

            if !existing_files.contains(&new_filename) {
                existing_files.insert(new_filename.clone());
                return Ok(new_filename);
            }
        }

        Err(MoveError::UniqueFilenameExhausted(MAX_ATTEMPTS))
    }

    /// Invalidates the collision cache for a given directory
    fn invalidate_cache(&self, directory: &Path) {
        let mut cache = self.collision_cache.lock();
        cache.remove(directory);
        log::debug!("Invalidated collision cache for {:?}", directory);
    }

    /// Clears the entire collision cache
    pub fn clear_cache(&self) {
        let mut cache = self.collision_cache.lock();
        cache.clear();
        log::debug!("Cleared entire collision cache");
    }

    pub fn move_files_batch(
        &self,
        sources: Vec<PathBuf>,
        destination_dir: impl AsRef<Path>,
        category: Option<String>,
        dry_run: bool,
    ) -> Vec<MoveResult> {
        let destination_dir = destination_dir.as_ref();
        
        sources
            .into_iter()
            .map(|source| {
                self.move_file(&source, destination_dir, None, category.clone(), dry_run)
            })
            .collect()
    }
}

/// RAII guard to ensure temporary files are cleaned up
struct TempFileGuard {
    path: PathBuf,
}

impl TempFileGuard {
    fn new(path: &Path) -> Self {
        Self {
            path: path.to_path_buf(),
        }
    }
}

impl Drop for TempFileGuard {
    fn drop(&mut self) {
        if self.path.exists() {
            let _ = fs::remove_file(&self.path);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use std::io::Write;
    use tempfile::TempDir;

    #[test]
    fn test_move_file() {
        let temp_dir = TempDir::new().unwrap();
        let source_dir = temp_dir.path().join("source");
        let dest_dir = temp_dir.path().join("dest");
        
        fs::create_dir(&source_dir).unwrap();
        
        let source_file = source_dir.join("test.txt");
        let mut file = File::create(&source_file).unwrap();
        file.write_all(b"Hello, World!").unwrap();
        drop(file);

        let mover = FileMover::with_defaults();
        let result = mover.move_file(&source_file, &dest_dir, None, None, false);

        assert_eq!(result.status, MoveStatus::Success);
        assert!(!source_file.exists());
        assert!(dest_dir.join("test.txt").exists());
    }

    #[test]
    fn test_batch_move() {
        let temp_dir = TempDir::new().unwrap();
        let source_dir = temp_dir.path().join("source");
        let dest_dir = temp_dir.path().join("dest");
        
        fs::create_dir(&source_dir).unwrap();
        
        let mut sources = Vec::new();
        for i in 0..10 {
            let file_path = source_dir.join(format!("file_{}.txt", i));
            File::create(&file_path).unwrap();
            sources.push(file_path);
        }

        let mover = FileMover::with_defaults();
        let results = mover.move_files_batch(sources, &dest_dir, None, false);

        assert_eq!(results.len(), 10);
        assert!(results.iter().all(|r| r.status == MoveStatus::Success));
    }
}
