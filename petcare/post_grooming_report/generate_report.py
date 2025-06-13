from weasyprint import HTML
import os
import base64
from datetime import datetime
import subprocess
import tempfile

def generate_grooming_report(data=None):
    """
    Generate a Canva-like PDF grooming report with a light blue background.
    
    Args:
        data (dict): Dictionary containing the report data
    
    Returns:
        tuple: Paths to the generated PDF and PNG files
    """
    # Use sample data if none provided
    if data is None:
        data = {
            "pet_name": "Levi",
            "owner_name": "Devi",
            "grooming_date": "January 05, 2025",
            "pet_breed": "Shih tzu",
            "pet_gender": "Male",
            "pet_age": "4 years",
            "pet_birthday": "January 15, 2021",
            "package_name": "Full Groom Package",
            "pet_image": os.path.abspath("/home/frappe-user/frappe-bench/apps/petcare/petcare/post_grooming_report/coco.jpg"),
            "groomer_name": "Jane Smith",
            
            # Wellness check values (percentage of health - higher is better)
            "skin_health": "90",
            "coat_health": "85",
            "ear_health": "95",
            "eye_health": "90",
            "dental_health": "85",
            
            # Behavior and recommendations
            "behavior_notes": "was super playful and adorable during grooming!",
            "recommendations": "Suggestions: Regular grooming sessions to maintain health and happiness.",
            
            # Loyalty program
            "loyalty_points": "200",  # Current loyalty points
            "loyalty_message": "Claim Rs. 200 discount on your 3rd visit!"
        }
    
    # Format date if it's in ISO format
    try:
        if isinstance(data.get("grooming_date"), str) and "-" in data["grooming_date"]:
            date_obj = datetime.strptime(data["grooming_date"], "%Y-%m-%d")
            data["grooming_date"] = date_obj.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        pass  # Keep original format if conversion fails
    
    # Calculate loyalty position percentage based on points
    try:
        loyalty_points = int(data.get("loyalty_points", "0"))
        # Map points to position on the path (0-600 points to 0-100%)
        # Points: 0, 50, 200, 300, 450, 600
        if loyalty_points <= 0:
            position = 0
        elif loyalty_points <= 50:
            position = (loyalty_points / 50) * 20  # 0-20%
        elif loyalty_points <= 200:
            position = 20 + ((loyalty_points - 50) / 150) * 20  # 20-40%
        elif loyalty_points <= 300:
            position = 40 + ((loyalty_points - 200) / 100) * 20  # 40-60%
        elif loyalty_points <= 450:
            position = 60 + ((loyalty_points - 300) / 150) * 20  # 60-80%
        elif loyalty_points <= 600:
            position = 80 + ((loyalty_points - 450) / 150) * 20  # 80-100%
        else:
            position = 100
        
        # Round to nearest 10 to match CSS classes (position-0, position-10, etc.)
        position = round(position / 10) * 10
        data["loyalty_position"] = str(int(position))
    except (ValueError, TypeError):
        data["loyalty_position"] = "40"  # Default position
    
    # Get branding assets
    branding_dir = os.path.join(os.path.dirname(__file__), "branding")
    
    # Logo
    logo_path = os.path.join(branding_dir, "MP_Wordmark_Primary.svg")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
            data["logo"] = f"data:image/svg+xml;base64,{img_data}"
    else:
        data["logo"] = ""
    
    # Dog illustration
    dog_path = os.path.join(branding_dir, "MP_dogpeeping.svg")
    if os.path.exists(dog_path):
        with open(dog_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
            data["dog_illustration"] = f"data:image/svg+xml;base64,{img_data}"
    else:
        data["dog_illustration"] = ""
    
    # Cat illustration
    cat_path = os.path.join(branding_dir, "MP_catpeeping.svg")
    if os.path.exists(cat_path):
        with open(cat_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
            data["cat_illustration"] = f"data:image/svg+xml;base64,{img_data}"
    else:
        data["cat_illustration"] = ""
    
    # Convert pet image to base64 if it exists
    if "pet_image" in data and os.path.exists(data["pet_image"]):
        with open(data["pet_image"], "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode('utf-8')
            img_ext = os.path.splitext(data["pet_image"])[1].lstrip('.')
            data["pet_image_base64"] = f"data:image/{img_ext};base64,{img_data}"
    else:
        # Placeholder image if no image is provided
        data["pet_image_base64"] = ""
    
    # Read the HTML template
    html_template_path = os.path.join(os.path.dirname(__file__), "report_template.html")
    
    with open(html_template_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    
    # Replace placeholders with actual data
    for key, value in data.items():
        if isinstance(value, str):  # Only replace if value is a string
            html_content = html_content.replace(f"{{{{ {key} }}}}", value)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.dirname(__file__)
    pdf_output_file = os.path.join(output_dir, f"grooming_report_{timestamp}.pdf")
    png_output_file = os.path.join(output_dir, f"grooming_report_{timestamp}.png")
    
    # Generate PDF
    HTML(string=html_content).write_pdf(pdf_output_file)
    print(f"PDF generated successfully: {os.path.abspath(pdf_output_file)}")
    
    # Try different methods to generate PNG
    png_generated = False
    
    # Method 1: Try using wkhtmltoimage if available
    try:
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
            temp_html.write(html_content.encode('utf-8'))
            temp_html_path = temp_html.name
        
        # Check if wkhtmltoimage is installed
        subprocess.run(["which", "wkhtmltoimage"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Convert HTML to PNG using wkhtmltoimage
        subprocess.run([
            "wkhtmltoimage",
            "--quality", "90",
            "--width", "800",
            temp_html_path,
            png_output_file
        ], check=True)
        
        # Clean up temporary file
        os.unlink(temp_html_path)
        
        print(f"PNG image generated successfully: {os.path.abspath(png_output_file)}")
        png_generated = True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Method 2: Try using ImageMagick if available and Method 1 failed
    if not png_generated:
        try:
            # Check if ImageMagick is installed
            subprocess.run(["which", "convert"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Convert PDF to PNG using ImageMagick
            subprocess.run([
                "convert", 
                "-density", "150",  # Higher density for better quality
                "-quality", "90", 
                pdf_output_file + "[0]",  # First page only
                png_output_file
            ], check=True)
            
            print(f"PNG image generated successfully: {os.path.abspath(png_output_file)}")
            png_generated = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    
    # If no PNG was generated, inform the user
    if not png_generated:
        print("Warning: Could not generate PNG. Required tools are not installed.")
        print("To install required tools:")
        print("  - For wkhtmltoimage: sudo apt-get install wkhtmltopdf")
        print("  - For ImageMagick: sudo apt-get install imagemagick")
        return pdf_output_file, None
    
    return pdf_output_file, png_output_file

# Execute if run directly
if __name__ == "__main__":
    generate_grooming_report()
