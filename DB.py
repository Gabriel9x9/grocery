import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 启用外键约束（SQLite默认关闭）
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 按照依赖顺序创建表
    tables = [
        '''CREATE TABLE IF NOT EXISTS categories (
            categoryId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            image TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS users (
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT,
            email TEXT UNIQUE,
            firstName TEXT,
            lastName TEXT,
            role TEXT
        )''',
        
        '''CREATE TABLE IF NOT EXISTS products (
            productId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            image TEXT,
            mft DATE,
            exp DATE,
            stock INTEGER,
            categoryId INTEGER,
            unit TEXT,
            FOREIGN KEY(categoryId) REFERENCES categories(categoryId) ON DELETE CASCADE
        )''',
        
        '''CREATE TABLE IF NOT EXISTS kart (
            cartId INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER,
            productId INTEGER,
            name TEXT,
            price REAL,
            quantity INTEGER,
            FOREIGN KEY(userId) REFERENCES users(userId) ON DELETE CASCADE,
            FOREIGN KEY(productId) REFERENCES products(productId) ON DELETE CASCADE
        )''',
        
        '''CREATE TABLE IF NOT EXISTS orders (
            orderId INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER,
            name TEXT,
            price REAL,
            quantity INTEGER,
            date DATE,
            productId INTEGER,
            FOREIGN KEY(userId) REFERENCES users(userId),
            FOREIGN KEY(productId) REFERENCES products(productId)
        )''',
        
        '''CREATE TABLE IF NOT EXISTS requests (
            requestId INTEGER PRIMARY KEY AUTOINCREMENT,
            requestType TEXT,
            categoryId INTEGER,
            productId INTEGER,
            oldName TEXT,
            name TEXT,
            price REAL,
            image TEXT,
            mft DATE,
            exp DATE,
            stock INTEGER,
            userName TEXT,
            userId INTEGER,
            unit TEXT,
            FOREIGN KEY (categoryId) REFERENCES categories(categoryId),
            FOREIGN KEY (productId) REFERENCES products(productId),
            FOREIGN KEY (userId) REFERENCES users(userId)
        )'''
    ]
    
    for table in tables:
        try:
            cursor.execute(table)
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")
            conn.rollback()
    
    conn.close()

def create_admin_user():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 先删除已存在的admin用户（避免userId冲突）
    try:
        cursor.execute("DELETE FROM users WHERE email = 'as@as.as';")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting old admin: {e}")
        conn.rollback()
    
    admin_user = (
        'as@as.as',  # email
        'admin',      # password (建议使用hash)
        'admin',      # firstName
        'admin',      # lastName
        'admin'       # role
    )
    
    try:
        cursor.execute('''INSERT INTO users 
                        (email, password, firstName, lastName, role) 
                        VALUES (?, ?, ?, ?, ?)''', admin_user)
        conn.commit()
        print("Admin user created successfully.")
    except sqlite3.Error as e:
        print(f"Error creating admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    create_admin_user()
    print("Database initialization completed.")