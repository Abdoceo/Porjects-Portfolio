import cv2
import numpy as np

# Load the image
image = cv2.imread('saudi coins.jpg')
if image is None:
    print("Error: Image not found.")
    exit()

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Gaussian blur
blurred_gray = cv2.GaussianBlur(gray, (17, 17), 0)

# Detect circles using HoughCircles
circles = cv2.HoughCircles(
    blurred_gray, cv2.HOUGH_GRADIENT, 0.9,
    minDist=120, param1=50, param2=27,
    minRadius=90, maxRadius=150
)

print(f"circles = {circles}")

# Function to calculate average brightness
def average_brightness(image, circles, size):
    av_value = []
    for coords in circles[0, :]:
        x_min = max(0, int(coords[1] - size))
        x_max = min(image.shape[0], int(coords[1] + size))
        y_min = max(0, int(coords[0] - size))
        y_max = min(image.shape[1], int(coords[0] + size))
        col = np.mean(image[x_min:x_max, y_min:y_max])
        av_value.append(col)
    return av_value

# Function to get the radius of detected circles
def get_radius(circles):
    radius = []
    for coords in circles[0, :]:
        radius.append(int(coords[2]))
    return radius

# Check if circles are detected
if circles is not None:
    circles = np.uint16(np.around(circles))
    
    # Draw detected circles and annotate
    count = 1
    for i in circles[0, :]:
        center = (i[0], i[1])
        # Draw the circle center
        cv2.circle(image, center, 1, (0, 100, 100), 3)
        # Draw the circle outline
        radius = i[2]
        cv2.circle(image, center, radius, (255, 0, 255), 3)
        # cv2.putText(image,  str(count), (i[0],i[1] ), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        count += 1

    # Calculate radii and brightness
    radii = get_radius(circles)
    print("Radii of circles:", radii)

    brightness = average_brightness(image, circles, 20)
    brightness = [float(b) for b in brightness]  # Convert np.float64 to regular float
    print("Brightness values:", brightness)



# Assign fixed values for coins based on their order in the circles array
values = [200, 50, 10, 100, 25, 5, 50, 10, 25, 5]  # Values in halala

# Annotate the image with values and total
count_2 = 0
total_value = 0  # Sum of all coin values
font_scale = 1  # Default font scale
thickness = 2   # Default thickness

for i in circles[0, :]:
    coin_value = values[count_2]  # Get the assigned value for the current coin
    total_value += coin_value  # Add to the total

    # Determine the text to display based on the coin value
    if coin_value == 100:
        display_text = "1 Riyal"
    elif coin_value == 200:
        display_text = "2 Riyal"
    else:
        display_text = f"{coin_value}h"  # Default to halalas

    # Dynamically adjust font size based on circle radius
    radius = i[2]
    font_scale = max(0.5, radius / 100)  # Scale font size with a minimum of 0.5
    thickness = max(1, int(radius / 50))  # Scale thickness with a minimum of 1

    # Annotate each coin with its value
    cv2.putText(
        image, display_text, (i[0] - int(radius / 2), i[1]), 
        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness, cv2.LINE_AA
    )
    count_2 += 1

# Convert total value to Riyal for annotation
total_riyal = total_value / 100  # Convert halala to Riyal
cv2.putText(
    image, f"Total: {total_riyal:.2f} Riyal", (50, 50), 
    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA
)

print(f"Total Value: {total_riyal:.2f} Riyal")

# Display the final image
cv2.imshow("Detected Circles", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
