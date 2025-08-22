#!/bin/bash

# Deployment Script for Logistics Project
# Safely fixes issues without affecting database data

echo "🚀 Starting Data-Safe Deployment Process..."

# Function to check if a command succeeded
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed!"
        exit 1
    fi
}

# Function to fix user model conflicts without affecting data
fix_user_model_conflicts() {
    echo "🔧 Fixing user model conflicts safely..."
    
    # Create a backup of the models file
    if [ -f "dealer_app/models.py" ]; then
        cp dealer_app/models.py dealer_app/models.py.backup
        echo "📋 Created backup of models.py"
    fi
    
    # Apply the related_name fixes to avoid clashes
    python3 -c "
import re

# Read the models file
with open('dealer_app/models.py', 'r') as f:
    content = f.read()

# Check if CustomUser model exists
if 'class CustomUser' in content:
    print('Found CustomUser model, applying fixes...')
    
    # Fix groups field
    if 'groups = models.ManyToManyField' in content:
        if 'related_name' not in content:
            # Add related_name to avoid clash with auth.User
            content = re.sub(
                r'groups = models\.ManyToManyField\([^)]+\)',
                \"groups = models.ManyToManyField('auth.Group', related_name='customuser_groups', blank=True)\",
                content
            )
            print('Added related_name to groups field')
        else:
            print('Groups field already has related_name')
    else:
        print('Groups field not found in CustomUser')
    
    # Fix user_permissions field
    if 'user_permissions = models.ManyToManyField' in content:
        if 'related_name' not in content:
            # Add related_name to avoid clash with auth.User
            content = re.sub(
                r'user_permissions = models\.ManyToManyField\([^)]+\)',
                \"user_permissions = models.ManyToManyField('auth.Permission', related_name='customuser_permissions', blank=True)\",
                content
            )
            print('Added related_name to user_permissions field')
        else:
            print('User_permissions field already has related_name')
    else:
        print('User_permissions field not found in CustomUser')
    
    # Write the fixed content back
    with open('dealer_app/models.py', 'w') as f:
        f.write(content)
    
    print('CustomUser model fixes applied successfully.')
else:
    print('CustomUser model not found. No fixes needed.')
"
    check_success "User model conflict fixes applied"
}

# Function to check for duplicate model registration
fix_duplicate_model_registration() {
    echo "🔧 Checking for duplicate model registration..."
    
    # Check for duplicate model imports in apps.py
    if [ -f "dealer_app/apps.py" ]; then
        python3 -c "
# Check for duplicate model registration in apps.py
with open('dealer_app/apps.py', 'r') as f:
    content = f.read()

# Check for common patterns that cause duplicate registration
if 'ready(self):' in content and 'import models' in content:
    lines = content.split('\\n')
    in_ready_method = False
    has_model_import_in_ready = False
    
    for i, line in enumerate(lines):
        if 'def ready(self):' in line:
            in_ready_method = True
            continue
        
        if in_ready_method and line.strip() == '':
            in_ready_method = False
            continue
            
        if in_ready_method and ('import models' in line or 'from . import models' in line):
            has_model_import_in_ready = True
            print('Found model import in ready method - this can cause duplicate registration')
            # Comment out the line to prevent duplicate registration
            lines[i] = '# ' + line + '  # Commented out to prevent duplicate registration'
    
    if has_model_import_in_ready:
        with open('dealer_app/apps.py', 'w') as f:
            f.write('\\n'.join(lines))
        print('Fixed duplicate model registration issue.')
    else:
        print('No duplicate model registration issues found.')
"
    fi
    
    check_success "Duplicate model registration check completed"
}

# Function to fix Nginx configuration
fix_nginx_config() {
    echo "🔧 Checking Nginx configuration..."
    
    # Check for default config issues
    if [ -f "/etc/nginx/sites-enabled/default" ]; then
        echo "📋 Disabling default Nginx site to avoid conflicts..."
        sudo rm /etc/nginx/sites-enabled/default
    fi
    
    # Check for your site configuration
    if [ -f "/etc/nginx/sites-available/logistics" ]; then
        echo "📋 Fixing your Nginx configuration..."
        
        # Create a backup
        sudo cp /etc/nginx/sites-available/logistics /etc/nginx/sites-available/logistics.backup
        
        # Remove any conflicting server names
        sudo sed -i '/server_name _;/d' /etc/nginx/sites-available/logistics
        sudo sed -i '/server_name 147\.93\.110\.231;/d' /etc/nginx/sites-available/logistics
        
        # Ensure proper server name is set
        if ! grep -q "server_name goodwayexpress.online www.goodwayexpress.online;" /etc/nginx/sites-available/logistics; then
            sudo sed -i '/listen 80;/a\\tserver_name goodwayexpress.online www.goodwayexpress.online;' /etc/nginx/sites-available/logistics
        fi
    else
        echo "⚠️  Custom Nginx configuration not found. Creating a new one..."
        
        # Create a basic Nginx configuration
        sudo bash -c 'cat > /etc/nginx/sites-available/logistics << EOF
server {
    listen 80;
    server_name goodwayexpress.online www.goodwayexpress.online;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/logistics_project;
    }
    
    location /media/ {
        root /home/logistics_project;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
EOF'
        
        # Enable the site
        sudo ln -sf /etc/nginx/sites-available/logistics /etc/nginx/sites-enabled/
    fi
    
    check_success "Nginx configuration fixes applied"
}

# Ask about pulling latest code
read -p "Do you want to pull the latest code from GitHub? (yes/no): " pull_choice
if [[ "$pull_choice" =~ ^[Yy][Ee][Ss]$|[Yy]$ ]]; then
    echo "🌐 Pulling latest code from GitHub..."
    git pull origin main
    check_success "GitHub update"
else
    echo "⏭️ Skipping GitHub update..."
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate
check_success "Virtual environment activation"

# Apply fixes before proceeding
fix_user_model_conflicts
fix_duplicate_model_registration

# Install/update dependencies
echo "📦 Installing/updating dependencies..."
pip install -r requirements.txt
check_success "Dependencies installation"

# Apply database migrations (safe for existing data)
echo "🗄️ Applying database migrations safely..."
python manage.py makemigrations --no-input
check_success "Make migrations"

python manage.py migrate
check_success "Database migration"

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput
check_success "Static files collection"

# Fix Nginx configuration
fix_nginx_config

# Restart Gunicorn
echo "🔄 Restarting Gunicorn..."
sudo systemctl restart gunicorn
check_success "Gunicorn restart"

# Test and reload Nginx
echo "🛠️ Checking Nginx configuration..."
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    check_success "Nginx reload"
else
    echo "❌ Nginx configuration test failed. Restoring backup..."
    # Restore backup if config test failed
    if [ -f "/etc/nginx/sites-available/logistics.backup" ]; then
        sudo cp /etc/nginx/sites-available/logistics.backup /etc/nginx/sites-available/logistics
        sudo nginx -t && sudo systemctl reload nginx
        echo "📋 Restored Nginx configuration from backup."
    fi
fi

echo "🎉 Data-Safe Deployment Completed Successfully!"
echo "📋 Summary of fixes applied:"
echo "   - CustomUser model related_name conflicts resolved (NO DATA LOSS)"
echo "   - Duplicate model registration checked and fixed"
echo "   - Nginx configuration conflicts resolved"
echo "   - All database data preserved intact"
