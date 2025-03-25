#include <memory>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/pose_array.hpp>

/**
 * @class HelperPublishBase
 */
class HelperPublishBase : public rclcpp::Node
{
public:
  HelperPublishBase()
  : Node("helper_publisher")
  {
    body_pose_array_topic_ = "body_pose_array";
    body_pose_topic_ = "body_pose";
    sub_pose_array_ = this->create_subscription<geometry_msgs::msg::PoseArray>(body_pose_array_topic_, 
           10, std::bind(&HelperPublishBase::odom_cb, this, std::placeholders::_1) );
    pub_pose_ = this->create_publisher<geometry_msgs::msg::Pose>(body_pose_topic_, 10);
  }

  void odom_cb( const geometry_msgs::msg::PoseArray &_poses) 
  {
     //RCLCPP_INFO(this->get_logger(), "Got odom pose array, get one and republish");
     geometry_msgs::msg::Pose msg;
     if(_poses.poses.size() > 0)
     {
       msg = _poses.poses[0];
       pub_pose_->publish(msg);
     }
  };


private:
  rclcpp::Subscription<geometry_msgs::msg::PoseArray>::SharedPtr sub_pose_array_;
  rclcpp::Publisher<geometry_msgs::msg::Pose>::SharedPtr pub_pose_;
  std::string body_pose_array_topic_;
  std::string body_pose_topic_;
};


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<HelperPublishBase>());
  rclcpp::shutdown();
  return 0;
}
