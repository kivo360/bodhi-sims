pub mod state;

pub trait StateEngine {
    pub fn new() -> Self;
    pub fn push(&mut self, state: State);
    pub fn latest(&self) -> &State;
}
