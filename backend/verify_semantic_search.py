import sys
import os

# Align python path to backend
backend_path = os.path.dirname(os.path.abspath(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from embedding_service import embedding_service
from semantic_search import search_policy

from pdf_processor import clean_text, repair_broken_words

def main():
    print("Testing clean_text and repair_broken_words...")
    # Test cleaning extra whitespace
    assert clean_text("  hello   world  ") == "hello world"
    
    # Test word repairing
    assert repair_broken_words("Hospi talization") == "Hospitalization"
    assert repair_broken_words("t reatment") == "treatment"
    assert repair_broken_words("diagnos tic") == "diagnostic"
    assert repair_broken_words("co payment") == "co-payment"
    assert repair_broken_words("pre existing") == "pre-existing"
    print("Clean_text and repair_broken_words tests passed successfully!")
    
    print("Initializing test chunks...")
    
    # 1. Prepare dummy chunks representing parsed PDF text
    dummy_chunks = [
        {
            "heading": "General outpatient care",
            "text": "This insurance policy covers standard outpatient care, primary physician consultations, and annual physical checkups. Prescriptions are covered up to a limit of $500 per member per fiscal year.",
            "page": 3
        },
        {
            "heading": "Exclusions - Surgery",
            "text": "Knee surgery, arthroscopy, and other joint replacement procedures are fully excluded from standard coverage. For orthopedic surgery options, a premium medical rider must be active.",
            "page": 12
        },
        {
            "heading": "Dental Options",
            "text": "Dental care options, including cleanings, fillings, root canals, and orthodontic braces, require a separate dental plan option. Routine dental cleanings are covered up to 50% under Plan B.",
            "page": 18
        },
        {
            "heading": "3.51 Room Rent",
            "text": "3.51 Room Rent\nRoom rent, boarding, and nursing expenses are covered up to a limit of 1% of the sum insured per day of hospitalization.",
            "page": 5
        },
        {
            "heading": "4.3 Cataract Treatment",
            "text": "4.3 Cataract Treatment\nCataract surgery and treatment costs are covered up to a sub-limit of INR 50,000 per eye per policy year.",
            "page": 8
        },
        {
            "heading": "5.1 Organ Donor Expenses",
            "text": "5.1 Organ Donor Expenses\nHospitalization expenses incurred on the donor for harvesting the organ during an organ transplant are covered up to the sum insured.",
            "page": 11
        },
        {
            "heading": "7.3 Obesity / Weight Control",
            "text": "7.3 Obesity / Weight Control\nTreatment of obesity, weight control programs, and bariatric surgery are excluded under this policy unless medically mandated.",
            "page": 15
        },
        {
            "heading": "3.2 Waiting Period",
            "text": "3.2 Waiting Period\nPre-existing disease waiting period of 36 months applies from the inception of the policy. Specific diseases list waiting period of 24 months.",
            "page": 20
        },
        {
            "heading": "5.6 Road Ambulance Charges",
            "text": "5.6 Road Ambulance Charges\nAmbulance charges for transferring the insured to a hospital in case of emergency are covered up to INR 2,000 per hospitalization.",
            "page": 13
        },
        {
            "heading": "3.12 Domiciliary Hospitalization",
            "text": "3.12 Domiciliary Hospitalization\nDomiciliary hospitalization covers medical treatment for a period exceeding three days for an illness which would normally require care at a hospital but is taken at home.",
            "page": 7
        }
    ]

    print("Generating embeddings and writing into cache...")
    try:
        embedding_service.embed_chunks_and_cache(dummy_chunks, "test_policy.pdf")
        print("Embeddings loaded in memory cache successfully.")
    except Exception as e:
        print(f"Error during caching: {str(e)}")
        return

    # Verify state flags
    print(f"Model loaded: {embedding_service.is_model_loaded()}")
    print(f"Document uploaded: {embedding_service.is_document_uploaded()}")

    # 2. Run queries
    queries = [
        "Pre-existing disease waiting period",
        "Room rent limit",
        "Ambulance charges",
        "Domiciliary hospitalization"
    ]

    for query in queries:
        print(f"\nQuerying: '{query}'")
        try:
            res = search_policy(query)
            print("Response Result:")
            print(f"  Status: {res['status']}")
            print(f"  Similarity: {res['similarity']}%")
            print(f"  Page: {res['page']}")
            print(f"  Highlighted Sentence: '{res['highlighted_sentence']}'")
            print(f"  Context Answer: {res['answer']}")
        except Exception as e:
            print(f"Error running search query: {str(e)}")

if __name__ == "__main__":
    main()
