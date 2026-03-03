use std::sync::Arc;
use parking_lot::Mutex;
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone, Debug)]
pub struct ProgressInfo {
    #[pyo3(get)]
    pub current_file: String,
    
    #[pyo3(get)]
    pub files_completed: usize,
    
    #[pyo3(get)]
    pub files_total: usize,
    
    #[pyo3(get)]
    pub bytes_transferred: u64,
    
    #[pyo3(get)]
    pub bytes_total: u64,
    
    #[pyo3(get)]
    pub current_file_progress: f64,  // 0.0 to 1.0
    
    #[pyo3(get)]
    pub stage: String,  // "validating", "copying", "verifying", "complete"
}

#[pymethods]
impl ProgressInfo {
    fn __repr__(&self) -> String {
        format!(
            "ProgressInfo(file={}/{}, bytes={}/{}, progress={:.1}%, stage={})",
            self.files_completed,
            self.files_total,
            self.bytes_transferred,
            self.bytes_total,
            self.current_file_progress * 100.0,
            self.stage
        )
    }
    
    /// Get overall progress as a percentage
    #[getter]
    fn overall_progress(&self) -> f64 {
        if self.files_total == 0 {
            return 0.0;
        }
        
        let files_progress = self.files_completed as f64 / self.files_total as f64;
        let current_file_contribution = if self.files_total > 0 {
            self.current_file_progress / self.files_total as f64
        } else {
            0.0
        };
        
        (files_progress + current_file_contribution) * 100.0
    }
}

/// Python callback wrapper for progress reporting
pub struct ProgressCallback {
    callback: Arc<Mutex<Option<PyObject>>>,
}

impl ProgressCallback {
    pub fn new() -> Self {
        Self {
            callback: Arc::new(Mutex::new(None)),
        }
    }
    
    pub fn set_callback(&self, callback: PyObject) {
        *self.callback.lock() = Some(callback);
    }
    
    pub fn clear_callback(&self) {
        *self.callback.lock() = None;
    }
    
    /// Report progress to Python callback if set
    pub fn report(&self, info: ProgressInfo) -> PyResult<()> {
        let callback_guard = self.callback.lock();
        if let Some(ref callback) = *callback_guard {
            Python::with_gil(|py| {
                let py_info = Py::new(py, info)?;
                callback.call1(py, (py_info,))?;
                Ok::<(), PyErr>(())
            })?;
        }
        Ok(())
    }
}

impl Clone for ProgressCallback {
    fn clone(&self) -> Self {
        Self {
            callback: Arc::clone(&self.callback),
        }
    }
}

impl Default for ProgressCallback {
    fn default() -> Self {
        Self::new()
    }
}

pub fn make_progress_info(
    current_file: String,
    files_completed: usize,
    files_total: usize,
    bytes_transferred: u64,
    bytes_total: u64,
    current_file_progress: f64,
    stage: &str,
) -> ProgressInfo {
    ProgressInfo {
        current_file,
        files_completed,
        files_total,
        bytes_transferred,
        bytes_total,
        current_file_progress: current_file_progress.clamp(0.0, 1.0),
        stage: stage.to_string(),
    }
}
