from services.bedrock_image import generate_image


prompt = (
    "A professional advertising photograph of a futuristic creative studio, "
    "realistic style, clean composition, cinematic lighting"
)

image_bytes = generate_image(prompt)

with open("generated_image_service.png", "wb") as file:
    file.write(image_bytes)

print("Imagen generada correctamente.")