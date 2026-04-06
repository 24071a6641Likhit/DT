#!/bin/bash

set -e

echo "========================================="
echo "Module 10: Frontend Dashboard Verification"
echo "========================================="
echo ""

cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found. Please run 'npm install' first."
    exit 1
fi
echo "✅ node_modules exists"

# Check required files exist
echo ""
echo "Checking required files..."
files=(
    "src/services/api.js"
    "src/hooks/useSSE.js"
    "src/utils/formatters.js"
    "src/components/DeviceCard.jsx"
    "src/components/AlertCard.jsx"
    "src/components/PowerChart.jsx"
    "src/pages/Dashboard.jsx"
    "src/pages/Alerts.jsx"
    "src/pages/Billing.jsx"
    "src/App.jsx"
    "src/App.css"
    "src/main.jsx"
    "index.html"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
        exit 1
    fi
done

# Check if .env file exists
if [ -f ".env" ]; then
    echo "  ✅ .env"
    if grep -q "VITE_API_URL" .env; then
        echo "     API URL configured: $(grep VITE_API_URL .env)"
    fi
else
    echo "  ⚠️  .env not found (optional)"
fi

echo ""
echo "Running build test..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful"
else
    echo "❌ Build failed"
    exit 1
fi

# Check build output
if [ -d "dist" ]; then
    echo "✅ dist/ folder created"
    
    # Calculate bundle size
    total_size=$(du -sh dist | cut -f1)
    echo "   Bundle size: $total_size"
    
    # Count files
    file_count=$(find dist -type f | wc -l)
    echo "   Files generated: $file_count"
    
    # Check for key files
    if [ -f "dist/index.html" ]; then
        echo "   ✅ index.html"
    fi
    if ls dist/assets/*.js 1> /dev/null 2>&1; then
        echo "   ✅ JavaScript bundles"
    fi
    if ls dist/assets/*.css 1> /dev/null 2>&1; then
        echo "   ✅ CSS bundles"
    fi
else
    echo "❌ dist/ folder not created"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Module 10 verification complete!"
echo "========================================="
echo ""
echo "Frontend is ready. To start development server:"
echo "  npm run dev"
echo ""
echo "To preview production build:"
echo "  npm run preview"
echo ""
echo "Make sure the backend is running at http://localhost:8000"
