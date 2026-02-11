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

-- TestAssignment table
CREATE TABLE test_assignment (
    id SERIAL PRIMARY KEY,
    test_id INTEGER NOT NULL REFERENCES deck(id),
    group_id INTEGER REFERENCES study_group(id),
    student_id INTEGER REFERENCES "user"(id),
    assigned_by INTEGER NOT NULL REFERENCES "user"(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP
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

-- TestResult table
CREATE TABLE test_result (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES test_assignment(id),
    student_id INTEGER NOT NULL REFERENCES "user"(id),
    score FLOAT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);