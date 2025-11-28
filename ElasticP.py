from elasticsearch import Elasticsearch, helpers
import sys

try:
    client = Elasticsearch(
        "https://cfaacd33313f4cecbc9d83ec9c36768d.us-central1.gcp.cloud.es.io:443",
        api_key="Tk5wR3VKb0JWQ1g1TVFnUHNuV3g6MnlYN3Y0NURmbVktcGRlVGpFUGVDQQ==",
    )
    
    # Verificar la conexión
    if not client.ping():
        print("Error: No se pudo conectar a Elasticsearch")
        sys.exit(1)
    
    index_name = "prueba_index"

    docs = [
        {
            "_index": index_name,
            "_source": {
                "text": "Yellowstone National Park is one of the largest national parks in the United States. It ranges from the Wyoming to Montana and Idaho, and contains an area of 2,219,791 acress across three different states. Its most famous for hosting the geyser Old Faithful and is centered on the Yellowstone Caldera, the largest super volcano on the American continent. Yellowstone is host to hundreds of species of animal, many of which are endangered or threatened. Most notably, it contains free-ranging herds of bison and elk, alongside bears, cougars and wolves. The national park receives over 4.5 million visitors annually and is a UNESCO World Heritage Site."
            }
        },
        {
            "_index": index_name,
            "_source": {
                "text": "Yosemite National Park is a United States National Park, covering over 750,000 acres of land in California. A UNESCO World Heritage Site, the park is best known for its granite cliffs, waterfalls and giant sequoia trees. Yosemite hosts over four million visitors in most years, with a peak of five million visitors in 2016. The park is home to a diverse range of wildlife, including mule deer, black bears, and the endangered Sierra Nevada bighorn sheep. The park has 1,200 square miles of wilderness, and is a popular destination for rock climbers, with over 3,000 feet of vertical granite to climb. Its most famous and cliff is the El Capitan, a 3,000 feet monolith along its tallest face."
            }
        },
        {
            "_index": index_name,
            "_source": {
                "text": "Rocky Mountain National Park is one of the most popular national parks in the United States. It receives over 4.5 million visitors annually, and is known for its mountainous terrain, including Longs Peak, which is the highest peak in the park. The park is home to a variety of wildlife, including elk, mule deer, moose, and bighorn sheep. The park is also home to a variety of ecosystems, including montane, subalpine, and alpine tundra. The park is a popular destination for hiking, camping, and wildlife viewing, and is a UNESCO World Heritage Site."
            }
        }
    ]

    # Timeout para permitir la carga del modelo de machine learning
    ingestion_timeout = 300

    bulk_response = helpers.bulk(
        client.options(request_timeout=ingestion_timeout),
        docs
    )
    
    print(f"Documentos indexados: {bulk_response[0]}")
    if bulk_response[1]:
        print("Errores encontrados:")
        for error in bulk_response[1]:
            print(error)

except Exception as e:
    print(f"Error: {e}")