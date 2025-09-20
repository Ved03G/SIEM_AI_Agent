from opensearchpy import OpenSearch

# !!! EDIT THIS LINE WITH THE PASSWORD THAT WORKED IN CURL !!!
PASSWORD = "your-correct-password-here"

print("--- Running Minimal Connection Test with OpenSearch client ---")

try:
    # We are now using the correct OpenSearch client
    client = OpenSearch(
        hosts=[{'host': 'localhost', 'port': 9200}],
        http_auth=("admin", "SecretPassword"),  # Use the correct password here
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False
    )

    # The .info() call is a basic health check
    info = client.info()
    
    print("✅✅✅ CONNECTION SUCCESSFUL! ✅✅✅")
    print(info)

except Exception as e:
    print("❌❌❌ CONNECTION FAILED. ❌❌❌")
    print(f"\nThe error is: {e}")

print("\n--- Test Complete ---")