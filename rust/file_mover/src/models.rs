use std::path::PathBuf;
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MoveStatus {
    Success,
    Failed,
    Skipped,
    DryRun,
}

#[derive(Debug)]
pub struct MoveResult {
    pub status: MoveStatus,
    pub source: PathBuf,
    pub destination: Option<PathBuf>,
    pub category: Option<String>,
    pub error: Option<MoveError>,
}

impl MoveResult {
    pub fn success(source: PathBuf, destination: PathBuf, category: Option<String>) -> Self {
        Self {
            status: MoveStatus::Success,
            source,
            destination: Some(destination),
            category,
            error: None,
        }
    }

    pub fn dry_run(source: PathBuf, destination: PathBuf, category: Option<String>) -> Self {
        Self {
            status: MoveStatus::DryRun,
            source,
            destination: Some(destination),
            category,
            error: None,
        }
    }

    pub fn failed(source: PathBuf, category: Option<String>, error: MoveError) -> Self {
        Self {
            status: MoveStatus::Failed,
            source,
            destination: None,
            category,
            error: Some(error),
        }
    }

    pub fn skipped(source: PathBuf, destination: PathBuf, category: Option<String>) -> Self {
        Self {
            status: MoveStatus::Skipped,
            source,
            destination: Some(destination),
            category,
            error: None,
        }
    }
}

#[derive(Debug, Error)]
pub enum MoveError {
    #[error("Source file does not exist: {0}")]
    SourceNotFound(PathBuf),

    #[error("Source path is not a file: {0}")]
    NotAFile(PathBuf),

    #[error("Permission denied: {0}")]
    PermissionDenied(String),

    #[error("File integrity check failed after move")]
    IntegrityCheckFailed,

    #[error("Unable to generate unique filename after {0} attempts")]
    UniqueFilenameExhausted(usize),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Unexpected error: {0}")]
    Other(String),
}
