from styx_msgs.msg import TrafficLight
import rospy
import yaml
import tensorflow as tf
import numpy as np
import os
import cv2

class TLClassifier(object):
    def __init__(self):
        self.session = None
        self.model_graph = None
        self.classes = {1: TrafficLight.GREEN, 2: TrafficLight.RED, 3: TrafficLight.YELLOW, 4: TrafficLight.UNKNOWN}
        
        config_string = rospy.get_param("/traffic_light_config")
        self.config = yaml.load(config_string)
        self.get_model(os.path.dirname(os.path.realpath(__file__)) + self.config['classifier_model'])
        
    def get_model(self, model_path):
        config = tf.ConfigProto()
        config.graph_options.optimizer_options.global_jit_level = tf.OptimizerOptions.ON_1

        self.model_graph = tf.Graph()
        with tf.Session(graph=self.model_graph, config=config) as sess:
            self.session = sess
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(model_path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
                
    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        # Processing pre image
        image = cv2.resize(image, (300, 300))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        image_tensor = self.model_graph.get_tensor_by_name('image_tensor:0')
        detection_boxes = self.model_graph.get_tensor_by_name('detection_boxes:0')
        detection_scores = self.model_graph.get_tensor_by_name('detection_scores:0')
        detection_classes = self.model_graph.get_tensor_by_name('detection_classes:0')
        

        (boxes, scores, classes) = self.session.run(
            [detection_boxes, detection_scores, detection_classes],
            feed_dict={image_tensor: np.expand_dims(image, axis=0)})
        
        boxes = np.squeeze(boxes)
        scores = np.squeeze(scores)
        classes = np.squeeze(classes)

        for element, box in enumerate(boxes):
            if scores[element] > 0.5:
                traffic_light_class = self.classes[classes[element]]
                rospy.logdebug("Detected traffic light is: %d", traffic_light_class)
                return traffic_light_class
            else:
                rospy.logdebug("Traffic Light Image Unkown")
                
        return TrafficLight.UNKNOWN
