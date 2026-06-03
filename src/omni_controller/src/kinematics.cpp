#include <chrono>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

#include <Eigen/Dense>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "std_msgs/msg/float64_multi_array.hpp"
#include <tf2/LinearMath/Matrix3x3.h>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_ros/transform_broadcaster.h>

using namespace std::chrono_literals;

class OmniKinematics : public rclcpp::Node
{
  struct RobotConfig
  {
    int wheel_count;
    double heading_offset;
  };

  static constexpr double kWheelRadius = 0.03;
  static constexpr double kRobotRadius = 0.088;
  static constexpr double kPi = 3.14159265358979323846;

  const std::unordered_map<std::string, RobotConfig> kRobotModels = {
    {"3wheel", {3, 0.0}},
    {"4wheel", {4, -45.0}},
  };

public:
  explicit OmniKinematics(const std::string & robot_model)
  : Node("omni_kinematics")
  {
    if (kRobotModels.find(robot_model) == kRobotModels.end()) {
      std::string msg = "Unknown robot model: " + robot_model + "\nValid options are:\n";
      for (const auto & [name, _] : kRobotModels) {
        msg += "  - " + name + "\n";
      }
      throw std::invalid_argument(msg);
    }

    const auto & config = kRobotModels.at(robot_model);
    num_wheels_ = config.wheel_count;
    heading_offset_ = config.heading_offset;

    transform_matrix_ = build_transform_matrix(num_wheels_, heading_offset_);
    auto full_inverse = pseudo_inverse(transform_matrix_);
    odom_matrix_ = full_inverse.block(0, 0, 2, full_inverse.cols());

    for (int i = 1; i <= num_wheels_; ++i) {
      std::string joint_name = "omni_wheel_joint_" + std::to_string(i);
      joint_index_map_[joint_name] = i - 1;
    }

    for (int i = 0; i < num_wheels_; ++i) {
      std::string topic = "wheel" + std::to_string(i + 1) + "_controller/commands";
      wheel_pubs_.push_back(
        this->create_publisher<std_msgs::msg::Float64MultiArray>(topic, 10));
    }

    odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("odom", 10);
    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(*this);

    cmd_vel_sub_ = this->create_subscription<geometry_msgs::msg::Twist>(
      "cmd_vel", 10,
      std::bind(&OmniKinematics::cmd_vel_callback, this, std::placeholders::_1));

    joint_state_sub_ = this->create_subscription<sensor_msgs::msg::JointState>(
      "joint_states", 10,
      std::bind(&OmniKinematics::joint_state_callback, this, std::placeholders::_1));

    imu_sub_ = this->create_subscription<sensor_msgs::msg::Imu>(
      "imu", 10,
      std::bind(&OmniKinematics::imu_callback, this, std::placeholders::_1));

    last_time_ = this->get_clock()->now();
  }

private:
  int num_wheels_;
  double heading_offset_;

  Eigen::MatrixXd transform_matrix_;
  Eigen::MatrixXd odom_matrix_;
  std::unordered_map<std::string, int> joint_index_map_;

  std::vector<rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr> wheel_pubs_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_sub_;
  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;

  double pos_x_ = 0.0;
  double pos_y_ = 0.0;
  double vel_x_ = 0.0;
  double vel_y_ = 0.0;
  double yaw_ = 0.0;
  double angular_vel_z_ = 0.0;
  rclcpp::Time last_time_;

  void cmd_vel_callback(const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    Eigen::Vector3d cmd(msg->linear.x, msg->linear.y, msg->angular.z);
    Eigen::VectorXd wheel_speeds = transform_matrix_ * cmd;
    publish_wheel_speeds(wheel_speeds);
  }

  void joint_state_callback(const sensor_msgs::msg::JointState::SharedPtr msg)
  {
    Eigen::VectorXd wheel_vel(num_wheels_);
    wheel_vel.setZero();

    for (size_t i = 0; i < msg->name.size(); ++i) {
      auto it = joint_index_map_.find(msg->name[i]);
      if (it != joint_index_map_.end()) {
        wheel_vel(it->second) = msg->velocity[i];
      }
    }

    rclcpp::Time current_time = this->get_clock()->now();
    double dt = (current_time - last_time_).seconds();
    last_time_ = current_time;

    Eigen::Matrix2d rotation;
    rotation << std::cos(yaw_), -std::sin(yaw_),
                std::sin(yaw_),  std::cos(yaw_);
    Eigen::VectorXd dp = rotation * odom_matrix_ * wheel_vel * dt;

    pos_x_ += dp(0);
    pos_y_ += dp(1);

    if (dt > 0.0) {
      vel_x_ = dp(0) / dt;
      vel_y_ = dp(1) / dt;
    }

    publish_odom(current_time);
  }

  void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    angular_vel_z_ = msg->angular_velocity.z;

    tf2::Quaternion q(
      msg->orientation.x,
      msg->orientation.y,
      msg->orientation.z,
      msg->orientation.w);

    double roll, pitch;
    tf2::Matrix3x3(q).getRPY(roll, pitch, yaw_);
  }

  void publish_odom(const rclcpp::Time & stamp)
  {
    tf2::Quaternion q;
    q.setRPY(0.0, 0.0, yaw_);

    nav_msgs::msg::Odometry odom;
    odom.header.stamp = stamp;
    odom.header.frame_id = "odom";
    odom.child_frame_id = "base_footprint";
    odom.pose.pose.position.x = pos_x_;
    odom.pose.pose.position.y = pos_y_;
    odom.pose.pose.position.z = 0.0;
    odom.pose.pose.orientation.x = q.x();
    odom.pose.pose.orientation.y = q.y();
    odom.pose.pose.orientation.z = q.z();
    odom.pose.pose.orientation.w = q.w();
    odom.twist.twist.linear.x = vel_x_;
    odom.twist.twist.linear.y = vel_y_;
    odom.twist.twist.angular.z = angular_vel_z_;

    odom_pub_->publish(odom);

    geometry_msgs::msg::TransformStamped tf;
    tf.header.stamp = stamp;
    tf.header.frame_id = "odom";
    tf.child_frame_id = "base_footprint";
    tf.transform.translation.x = pos_x_;
    tf.transform.translation.y = pos_y_;
    tf.transform.translation.z = 0.0;
    tf.transform.rotation = odom.pose.pose.orientation;

    tf_broadcaster_->sendTransform(tf);
  }

  void publish_wheel_speeds(const Eigen::VectorXd & speeds)
  {
    for (int i = 0; i < speeds.size(); ++i) {
      std_msgs::msg::Float64MultiArray msg;
      msg.data = {speeds(i)};
      wheel_pubs_[i]->publish(msg);
    }
  }

  Eigen::MatrixXd build_transform_matrix(int n, double offset_deg) const
  {
    Eigen::MatrixXd m = Eigen::MatrixXd::Zero(n, 3);
    double angle_step = 360.0 / n;
    for (int i = 0; i < n; ++i) {
      double angle_rad = (angle_step * i + offset_deg) * kPi / 180.0;
      m(i, 0) = -std::sin(angle_rad) / kWheelRadius;
      m(i, 1) =  std::cos(angle_rad) / kWheelRadius;
      m(i, 2) =  kRobotRadius / kWheelRadius;
    }
    return m;
  }

  static Eigen::MatrixXd pseudo_inverse(const Eigen::MatrixXd & a, double tol = 1e-8)
  {
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(a, Eigen::ComputeThinU | Eigen::ComputeThinV);
    const auto & sv = svd.singularValues();
    Eigen::MatrixXd s_inv = Eigen::MatrixXd::Zero(svd.matrixV().cols(), svd.matrixU().cols());
    for (int i = 0; i < sv.size(); ++i) {
      if (sv(i) > tol) {
        s_inv(i, i) = 1.0 / sv(i);
      }
    }
    return svd.matrixV() * s_inv * svd.matrixU().transpose();
  }
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  const char * env_model = std::getenv("OMNI_ROBOT_MODEL");
  std::string robot_model = env_model ? env_model : "3wheel";

  rclcpp::spin(std::make_shared<OmniKinematics>(robot_model));
  rclcpp::shutdown();
  return 0;
}
