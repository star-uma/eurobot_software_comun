import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class LidarFilter(Node):
    def __init__(self):
        super().__init__('lidar_filter_node')
        self.subscription = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.publisher = self.create_publisher(LaserScan, '/scan_filtered', 10)
        self.distancia_maxima = 1.0 

    def scan_cb(self, msg: LaserScan):
        filtered_msg = msg
        filtered_ranges = []
        
        for r in msg.ranges:
            if r > self.distancia_maxima:
                filtered_ranges.append(float('inf'))
            else:
                filtered_ranges.append(r)
                
        filtered_msg.ranges = filtered_ranges
        filtered_msg.range_max = self.distancia_maxima
        self.publisher.publish(filtered_msg)

def main(args=None):
    rclpy.init(args=args)
    node = LidarFilter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

