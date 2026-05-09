#!/usr/bin/env python3
"""
Test script per verificare il rilevamento pagine bianche
Crea immagini di test e verifica che is_blank_page() funzioni correttamente
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import tempfile

# Aggiungi path per importare da scanner_service
sys.path.insert(0, str(Path(__file__).parent))

from scripts.scanner_service import is_blank_page


def create_test_images():
    """Crea immagini di test con diversi livelli di contenuto"""
    
    temp_dir = Path(tempfile.mkdtemp(prefix='blank_test_'))
    print(f"📁 Test images in: {temp_dir}\n")
    
    # A4 a 300 DPI = 2480x3508 pixel
    width, height = 2480, 3508
    
    tests = []
    
    # 1. Pagina completamente bianca
    img = Image.new('L', (width, height), color=255)
    path1 = temp_dir / 'test_1_blank_100.png'
    img.save(path1)
    tests.append(('100% Bianca', path1, True))
    
    # 2. Pagina quasi bianca (99%)
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)
    # Piccolo punto grigio
    draw.rectangle([1000, 1500, 1010, 1510], fill=200)
    path2 = temp_dir / 'test_2_almost_blank_99.png'
    img.save(path2)
    tests.append(('99% Bianca (punto)', path2, True))
    
    # 3. Pagina con testo piccolo (~95% bianca)
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)
    # Testo piccolo in alto
    for i in range(5):
        draw.rectangle([200, 200 + i*50, 600, 230 + i*50], fill=50)
    path3 = temp_dir / 'test_3_small_text_95.png'
    img.save(path3)
    tests.append(('95% Bianca (testo)', path3, False))
    
    # 4. Pagina grigia uniforme (non bianca)
    img = Image.new('L', (width, height), color=200)
    path4 = temp_dir / 'test_4_gray_uniform.png'
    img.save(path4)
    tests.append(('Grigia uniforme', path4, False))
    
    # 5. Pagina con contenuto normale
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)
    # Simula testo denso
    for i in range(50):
        y = 200 + i * 60
        draw.rectangle([200, y, 2200, y + 40], fill=50)
    path5 = temp_dir / 'test_5_normal_content.png'
    img.save(path5)
    tests.append(('Contenuto normale', path5, False))
    
    # 6. Pagina con bordo nero
    img = Image.new('L', (width, height), color=255)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width-1, height-1], outline=0, width=5)
    path6 = temp_dir / 'test_6_border.png'
    img.save(path6)
    tests.append(('Con bordo', path6, False))
    
    # 7. Pagina con rumore (artefatti scanner)
    img = Image.new('L', (width, height), color=255)
    import random
    pixels = img.load()
    # Aggiungi rumore sparse (0.1% pixel)
    for _ in range(int(width * height * 0.001)):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        pixels[x, y] = random.randint(230, 245)
    path7 = temp_dir / 'test_7_noise.png'
    img.save(path7)
    tests.append(('Con rumore 0.1%', path7, True))
    
    return tests, temp_dir


def run_tests():
    """Esegue i test di rilevamento pagine bianche"""
    
    print("🧪 Test Rilevamento Pagine Bianche\n")
    print("=" * 70)
    
    tests, temp_dir = create_test_images()
    
    passed = 0
    failed = 0
    
    for description, image_path, expected_blank in tests:
        result = is_blank_page(image_path)
        status = "✅ PASS" if result == expected_blank else "❌ FAIL"
        
        if result == expected_blank:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description:25} | Expected: {expected_blank:5} | Got: {result:5}")
        print(f"       | File: {image_path.name}")
        
        # Mostra statistiche dettagliate per i fallimenti
        if result != expected_blank:
            img = Image.open(image_path).convert('L')
            pixels = list(img.getdata())
            white_pixels = sum(1 for p in pixels if p > 240)
            white_ratio = white_pixels / len(pixels)
            
            import statistics
            variance = statistics.variance(pixels) if len(pixels) > 1 else 0
            
            print(f"       | Stats: white={white_ratio:.2%}, variance={variance:.2f}")
        
        print()
    
    print("=" * 70)
    print(f"\n📊 Risultati: {passed}/{len(tests)} test passati")
    
    if failed > 0:
        print(f"❌ {failed} test falliti!")
        print(f"\n💡 Considera di regolare i parametri in is_blank_page():")
        print(f"   - white_threshold (attuale: 0.98)")
        print(f"   - variance_threshold (attuale: 10.0)")
    else:
        print("✅ Tutti i test passati!")
    
    # Pulisci file di test
    import shutil
    try:
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up: {temp_dir}")
    except Exception as e:
        print(f"\n⚠️  Could not cleanup {temp_dir}: {e}")
    
    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
