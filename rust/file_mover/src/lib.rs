pub mod models;
pub mod mover;
pub mod options;
pub mod progress;

// Python bindings module
#[cfg(feature = "python")]
pub mod py_bindings;

// Re-export for Rust users
pub use models::{MoveError, MoveResult, MoveStatus};
pub use mover::FileMover;
pub use options::MoveOptions;

// Conditionally compile Python bindings
#[cfg(feature = "python")]
pub use py_bindings::*;
