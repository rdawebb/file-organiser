use pyo3::prelude::*;
use pyo3::exceptions::{PyIOError, PyPermissionError, PyFileNotFoundError, PyValueError};
use std::path::PathBuf;

use crate::models::{MoveError, MoveResult as RustMoveResult, MoveStatus as RustMoveStatus};
use crate::mover::FileMover as RustFileMover;
use crate::options::MoveOptions as RustMoveOptions;

#[pyclass(name = "MoveStatus")]
#[derive(Clone)]
pub struct PyMoveStatus {
    #[pyo3(get)]
    pub value: String,
}

#[pymethods]
impl PyMoveStatus {
    #[classattr]
    const SUCCESS: &'static str = "SUCCESS";
    
    #[classattr]
    const FAILED: &'static str = "FAILED";
    
    #[classattr]
    const DRY_RUN: &'static str = "DRY_RUN";

    fn __repr__(&self) -> String {
        format!("MoveStatus.{}", self.value)
    }

    fn __str__(&self) -> String {
        self.value.clone()
    }

    fn __eq__(&self, other: &Self) -> bool {
        self.value == other.value
    }
}

impl From<RustMoveStatus> for PyMoveStatus {
    fn from(status: RustMoveStatus) -> Self {
        let value = match status {
            RustMoveStatus::Success => "SUCCESS",
            RustMoveStatus::Failed => "FAILED",
            RustMoveStatus::Skipped => "SKIPPED",
            RustMoveStatus::DryRun => "DRY_RUN",
        };
        PyMoveStatus {
            value: value.to_string(),
        }
    }
}

#[pyclass(name = "MoveResult")]
pub struct PyMoveResult {
    #[pyo3(get)]
    pub status: PyMoveStatus,
    
    #[pyo3(get)]
    pub source: String,
    
    #[pyo3(get)]
    pub destination: Option<String>,
    
    #[pyo3(get)]
    pub category: Option<String>,
    
    #[pyo3(get)]
    pub error: Option<String>,
}

#[pymethods]
impl PyMoveResult {
    fn __repr__(&self) -> String {
        format!(
            "MoveResult(status={}, source='{}', destination={:?})",
            self.status.value, self.source, self.destination
        )
    }

    #[getter]
    fn is_success(&self) -> bool {
        self.status.value == "SUCCESS"
    }

    #[getter]
    fn is_failed(&self) -> bool {
        self.status.value == "FAILED"
    }

    #[getter]
    fn is_dry_run(&self) -> bool {
        self.status.value == "DRY_RUN"
    }
}

impl From<RustMoveResult> for PyMoveResult {
    fn from(result: RustMoveResult) -> Self {
        let error_msg = result.error.as_ref().map(|e| format!("{}", e));
        
        PyMoveResult {
            status: result.status.into(),
            source: result.source.to_string_lossy().to_string(),
            destination: result.destination.map(|p| p.to_string_lossy().to_string()),
            category: result.category,
            error: error_msg,
        }
    }
}

fn move_error_to_py_err(error: MoveError) -> PyErr {
    match error {
        MoveError::SourceNotFound(path) => {
            PyFileNotFoundError::new_err(format!(
                "Source file does not exist: {}",
                path.display()
            ))
        }
        MoveError::NotAFile(path) => {
            PyValueError::new_err(format!("Source path is not a file: {}", path.display()))
        }
        MoveError::PermissionDenied(msg) => {
            PyPermissionError::new_err(format!("Permission denied: {}", msg))
        }
        MoveError::IntegrityCheckFailed => {
            PyIOError::new_err("File integrity check failed after move")
        }
        MoveError::UniqueFilenameExhausted(attempts) => {
            PyValueError::new_err(format!(
                "Unable to generate unique filename after {} attempts",
                attempts
            ))
        }
        MoveError::Io(e) => PyIOError::new_err(format!("IO error: {}", e)),
        MoveError::Other(msg) => PyIOError::new_err(format!("Unexpected error: {}", msg)),
    }
}

#[pyclass(name = "MoveOptions")]
#[derive(Clone)]
pub struct PyMoveOptions {
    inner: RustMoveOptions,
}

#[pymethods]
impl PyMoveOptions {
    #[new]
    #[pyo3(signature = (atomic=true, verify_checksum=true, preserve_metadata=true, create_dirs=true, overwrite_existing=false))]
    fn new(
        atomic: bool,
        verify_checksum: bool,
        preserve_metadata: bool,
        create_dirs: bool,
        overwrite_existing: bool,
    ) -> Self {
        PyMoveOptions {
            inner: RustMoveOptions {
                atomic,
                verify_checksum,
                preserve_metadata,
                create_dirs,
                overwrite_existing,
            },
        }
    }

    #[getter]
    fn atomic(&self) -> bool {
        self.inner.atomic
    }

    #[setter]
    fn set_atomic(&mut self, value: bool) {
        self.inner.atomic = value;
    }

    #[getter]
    fn verify_checksum(&self) -> bool {
        self.inner.verify_checksum
    }

    #[setter]
    fn set_verify_checksum(&mut self, value: bool) {
        self.inner.verify_checksum = value;
    }

    #[getter]
    fn preserve_metadata(&self) -> bool {
        self.inner.preserve_metadata
    }

    #[setter]
    fn set_preserve_metadata(&mut self, value: bool) {
        self.inner.preserve_metadata = value;
    }

    #[getter]
    fn create_dirs(&self) -> bool {
        self.inner.create_dirs
    }

    #[setter]
    fn set_create_dirs(&mut self, value: bool) {
        self.inner.create_dirs = value;
    }

    #[getter]
    fn overwrite_existing(&self) -> bool {
        self.inner.overwrite_existing
    }

    #[setter]
    fn set_overwrite_existing(&mut self, value: bool) {
        self.inner.overwrite_existing = value;
    }

    fn __repr__(&self) -> String {
        format!(
            "MoveOptions(atomic={}, verify_checksum={}, preserve_metadata={}, create_dirs={}, overwrite_existing={})",
            self.inner.atomic,
            self.inner.verify_checksum,
            self.inner.preserve_metadata,
            self.inner.create_dirs,
            self.inner.overwrite_existing
        )
    }
}

#[pyclass(name = "FileMover")]
pub struct PyFileMover {
    inner: RustFileMover,
}

#[pymethods]
impl PyFileMover {
    #[new]
    #[pyo3(signature = (options=None))]
    fn new(options: Option<PyMoveOptions>) -> Self {
        let opts = options.map(|o| o.inner).unwrap_or_default();
        PyFileMover {
            inner: RustFileMover::new(opts),
        }
    }

    #[pyo3(signature = (source, destination_dir, filename=None, category=None, dry_run=false))]
    fn move_file(
        &self,
        source: String,
        destination_dir: String,
        filename: Option<String>,
        category: Option<String>,
        dry_run: bool,
    ) -> PyResult<PyMoveResult> {
        // Log the operation
        log::debug!(
            "Python called move_file: source={}, dest={}, dry_run={}",
            source,
            destination_dir,
            dry_run
        );

        let source_path = PathBuf::from(source);
        let dest_path = PathBuf::from(destination_dir);

        let result = self.inner.move_file(
            source_path,
            dest_path,
            filename.as_deref(),
            category,
            dry_run,
        );

        Ok(result.into())
    }

    #[pyo3(signature = (sources, destination_dir, category=None, dry_run=false))]
    fn move_files_batch(
        &self,
        sources: Vec<String>,
        destination_dir: String,
        category: Option<String>,
        dry_run: bool,
    ) -> PyResult<Vec<PyMoveResult>> {
        log::debug!(
            "Python called move_files_batch: {} files, dest={}, dry_run={}",
            sources.len(),
            destination_dir,
            dry_run
        );

        let dest_path = PathBuf::from(destination_dir);
        let source_paths: Vec<PathBuf> = sources.into_iter().map(PathBuf::from).collect();

        let results: Vec<PyMoveResult> = source_paths
            .into_iter()
            .map(|source| {
                self.inner
                    .move_file(&source, &dest_path, None, category.clone(), dry_run)
                    .into()
            })
            .collect();

        Ok(results)
    }

    fn clear_cache(&self) {
        log::debug!("Python called clear_cache");
        self.inner.clear_cache();
    }

    fn __repr__(&self) -> String {
        "FileMover()".to_string()
    }
}

#[pyfunction]
fn init_logging() -> PyResult<()> {
    pyo3_log::init();
    log::info!("Rust logging initialised and forwarded to Python");
    Ok(())
}

#[pyfunction]
fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// Python module definition
#[pymodule]
fn file_mover(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyFileMover>()?;
    m.add_class::<PyMoveOptions>()?;
    m.add_class::<PyMoveResult>()?;
    m.add_class::<PyMoveStatus>()?;

    m.add_function(wrap_pyfunction!(init_logging, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;

    // Add module-level constants
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}
