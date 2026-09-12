use std::time::Duration;

use ureq::Agent;

fn agent(secs: u64) -> Agent {
    ureq::AgentBuilder::new()
        .timeout(Duration::from_secs(secs))
        .build()
}

pub fn healthy(worker_url: &str) -> bool {
    agent(3)
        .get(&format!("{worker_url}/api/health"))
        .call()
        .is_ok()
}

pub fn start_processing(worker_url: &str, payload: &serde_json::Value) -> Result<(), String> {
    agent(15)
        .post(&format!("{worker_url}/api/generate"))
        .send_json(payload.clone())
        .map(|_| ())
        .map_err(|e| format!("worker generate: {e}"))
}