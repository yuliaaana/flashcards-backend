-- Add role to User
ALTER TABLE "user" ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'student';

-- StudyGroup table
CREATE TABLE study_group (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    teacher_id INTEGER NOT NULL REFERENCES "user"(id)
);

-- StudyGroupMembership table
CREATE TABLE study_group_membership (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_group(id),
    user_id INTEGER NOT NULL REFERENCES "user"(id),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignment table
CREATE TABLE assignment (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_group(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL REFERENCES "user"(id),
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AssignmentDeck table
CREATE TABLE assignment_deck (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id) ON DELETE CASCADE,
    deck_id INTEGER NOT NULL REFERENCES deck(id)
);

-- AssignmentMode table
CREATE TABLE assignment_mode (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id) ON DELETE CASCADE,
    mode VARCHAR(50) NOT NULL
);

-- AssignmentResult table
CREATE TABLE assignment_result (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES "user"(id),
    deck_id INTEGER NOT NULL REFERENCES deck(id),
    mode VARCHAR(50) NOT NULL,
    score FLOAT NOT NULL,
    total FLOAT NOT NULL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- StudyGroupDeck table
CREATE TABLE study_group_deck (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_group(id),
    deck_id INTEGER NOT NULL REFERENCES deck(id),
    added_by INTEGER NOT NULL REFERENCES "user"(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- StudyGroupFolder table
CREATE TABLE study_group_folder (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES study_group(id),
    folder_id INTEGER NOT NULL REFERENCES folder(id),
    added_by INTEGER NOT NULL REFERENCES "user"(id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- (Old test_result table removed, replaced by assignment_result above)