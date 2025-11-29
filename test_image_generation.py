import asyncio
import os
from AgneticFlow.image_generation import ImageGenerator
from dotenv import load_dotenv

load_dotenv()

async def test_image_generation():
    print("Testing ImageGenerator...")
    generator = ImageGenerator()
    
    product_url = "https://www.nike.com/t/air-force-1-07-mens-shoes-jBrhbr/CW2288-111"
    script = "Experience the classic comfort and style of the Nike Air Force 1 '07. Perfect for any occasion."
    
    print(f"Product URL: {product_url}")
    print(f"Script: {script}")
    
    try:
        images = generator.generate_ad_creatives(product_url, script, num_alterations=1)
        print(f"Generated images: {images}")
        
        if images:
            print("SUCCESS: Images generated.")
        else:
            print("FAILURE: No images generated.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_image_generation())
