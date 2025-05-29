// MongoDB initialization script for Agentic RAG System
// Developed by Atlas University, Istanbul, Türkiye

// Switch to the agentic_rag database
db = db.getSiblingDB('agentic_rag');

// Create collections for the Agentic RAG system
print('Creating collections for Agentic RAG system...');

// Create conversations collection for storing chat history
db.createCollection('conversations', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["session_id", "bot_name", "timestamp"],
            properties: {
                session_id: {
                    bsonType: "string",
                    description: "Session identifier for the conversation"
                },
                bot_name: {
                    bsonType: "string",
                    description: "Name of the bot handling the conversation"
                },
                user_message: {
                    bsonType: "string",
                    description: "User's message"
                },
                bot_response: {
                    bsonType: "string",
                    description: "Bot's response"
                },
                timestamp: {
                    bsonType: "date",
                    description: "Timestamp of the message"
                },
                metadata: {
                    bsonType: "object",
                    description: "Additional metadata"
                },
                tools_used: {
                    bsonType: "array",
                    description: "List of tools used in the response"
                },
                tool_outputs: {
                    bsonType: "object",
                    description: "Outputs from tools used"
                }
            }
        }
    }
});

// Create academic collections
db.createCollection('publications');
db.createCollection('conferences');
db.createCollection('journals');
db.createCollection('researchers');

// Create student collections
db.createCollection('courses');
db.createCollection('assignments');
db.createCollection('grades');
db.createCollection('students');

// Create administrative collections
db.createCollection('policies');
db.createCollection('announcements');
db.createCollection('departments');
db.createCollection('staff');

// Create vector embeddings collection for RAG
db.createCollection('usul_ve_esaslar-rag-chroma', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["page_content", "metadata", "embedding"],
            properties: {
                page_content: {
                    bsonType: "string",
                    description: "The text content of the document chunk"
                },
                metadata: {
                    bsonType: "object",
                    description: "Metadata about the document chunk"
                },
                embedding: {
                    bsonType: "array",
                    description: "Vector embedding of the content"
                }
            }
        }
    }
});

// Create indexes for better performance
print('Creating indexes...');

// Conversations indexes
db.conversations.createIndex({ "session_id": 1 });
db.conversations.createIndex({ "bot_name": 1 });
db.conversations.createIndex({ "timestamp": -1 });
db.conversations.createIndex({ "session_id": 1, "timestamp": -1 });

// Vector embeddings indexes
db['usul_ve_esaslar-rag-chroma'].createIndex({ "metadata.source": 1 });
db['usul_ve_esaslar-rag-chroma'].createIndex({ "metadata.page": 1 });

// Academic collections indexes
db.publications.createIndex({ "title": "text", "abstract": "text" });
db.publications.createIndex({ "authors": 1 });
db.publications.createIndex({ "publication_date": -1 });

db.researchers.createIndex({ "name": "text", "affiliation": "text" });
db.researchers.createIndex({ "research_areas": 1 });

// Student collections indexes
db.courses.createIndex({ "course_code": 1 });
db.courses.createIndex({ "course_name": "text" });
db.students.createIndex({ "student_id": 1 });

// Administrative collections indexes
db.policies.createIndex({ "title": "text", "content": "text" });
db.announcements.createIndex({ "date": -1 });
db.departments.createIndex({ "name": 1 });

// Insert sample data for testing
print('Inserting sample data...');

// Sample academic data
db.publications.insertMany([
    {
        title: "Artificial Intelligence in Education: A Comprehensive Review",
        authors: ["Dr. Mehmet Özkan", "Prof. Ayşe Demir"],
        abstract: "This paper reviews the current state of AI in educational systems...",
        publication_date: new Date("2024-01-15"),
        journal: "Turkish Journal of Educational Technology",
        keywords: ["AI", "Education", "Machine Learning"],
        language: "English"
    },
    {
        title: "Eğitimde Yapay Zeka Uygulamaları",
        authors: ["Dr. Fatma Yılmaz", "Doç. Dr. Ali Kaya"],
        abstract: "Bu çalışma eğitim sistemlerinde yapay zeka uygulamalarını incelemektedir...",
        publication_date: new Date("2024-02-20"),
        journal: "Türk Eğitim Teknolojileri Dergisi",
        keywords: ["Yapay Zeka", "Eğitim", "Teknoloji"],
        language: "Turkish"
    }
]);

// Sample course data
db.courses.insertMany([
    {
        course_code: "CS101",
        course_name: "Introduction to Computer Science",
        course_name_tr: "Bilgisayar Bilimine Giriş",
        credits: 3,
        semester: "Fall 2024",
        instructor: "Prof. Dr. Ahmet Yılmaz",
        description: "Basic concepts of computer science and programming",
        description_tr: "Bilgisayar bilimi ve programlamanın temel kavramları"
    },
    {
        course_code: "AI301",
        course_name: "Artificial Intelligence",
        course_name_tr: "Yapay Zeka",
        credits: 4,
        semester: "Spring 2024",
        instructor: "Dr. Zeynep Kara",
        description: "Introduction to AI concepts and applications",
        description_tr: "Yapay zeka kavramları ve uygulamalarına giriş"
    }
]);

// Sample policy data
db.policies.insertMany([
    {
        title: "Academic Integrity Policy",
        title_tr: "Akademik Dürüstlük Politikası",
        content: "All students must adhere to the highest standards of academic integrity...",
        content_tr: "Tüm öğrenciler en yüksek akademik dürüstlük standartlarına uymalıdır...",
        effective_date: new Date("2024-01-01"),
        category: "Academic",
        language: "Bilingual"
    }
]);

print('MongoDB initialization completed successfully!');
print('Collections created: conversations, publications, conferences, journals, researchers, courses, assignments, grades, students, policies, announcements, departments, staff, usul_ve_esaslar-rag-chroma');
print('Indexes created for optimal performance');
print('Sample data inserted for testing');
