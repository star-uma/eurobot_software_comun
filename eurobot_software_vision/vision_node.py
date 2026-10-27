import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        self.bridge = CvBridge()
        
        # API de OpenCV 4.5 (Compatible con ROS 2 Humble)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        
        self.get_logger().info("Módulo de visión inicializado. Esperando imágenes...")

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # En lugar de usar un objeto ArucoDetector, llamamos a la función global detectMarkers
        corners, ids, rejected = cv2.aruco.detectMarkers(
            cv_image, 
            self.aruco_dict, 
            parameters=self.aruco_params
        )

        if ids is not None:
            cv2.aruco.drawDetectedMarkers(cv_image, corners, ids)
            self.get_logger().info(f"Cajas detectadas (IDs): {ids.flatten()}")

        cv2.imshow("Eurobot - Vision Debug", cv_image)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()