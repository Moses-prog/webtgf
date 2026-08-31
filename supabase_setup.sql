CREATE TABLE users (
  chat_id TEXT PRIMARY KEY,
  data JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE platform_state (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL DEFAULT '{}'::jsonb
);


-- Map for mirror deletion
CREATE TABLE IF NOT EXISTS message_map (
    id SERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_channel_id TEXT NOT NULL,
    source_msg_id TEXT NOT NULL,
    target_channel_id TEXT NOT NULL,
    target_msg_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_source_msg ON message_map(source_channel_id, source_msg_id);
