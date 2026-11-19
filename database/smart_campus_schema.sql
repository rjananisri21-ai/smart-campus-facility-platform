-- ============================================================
-- Smart Campus Platform - MySQL Database Schema
-- Database: smart_campus
-- Generated for MySQL Workbench 8.0
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_campus DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_campus;

-- Table structure for campus_users
CREATE TABLE `campus_users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `role` varchar(20) NOT NULL,
  `department` varchar(100) NOT NULL,
  `phone_number` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `campus_users_role_872567df` (`role`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_facilities
CREATE TABLE `campus_facilities` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `facility_type` varchar(50) NOT NULL,
  `location` varchar(150) NOT NULL,
  `capacity` int unsigned NOT NULL,
  `status` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `campus_facilities_status_e19a92f2` (`status`),
  CONSTRAINT `campus_facilities_chk_1` CHECK ((`capacity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_bookings
CREATE TABLE `campus_bookings` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `start_time` datetime(6) NOT NULL,
  `end_time` datetime(6) NOT NULL,
  `purpose` varchar(255) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` bigint NOT NULL,
  `facility_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_bk_fac_time_stat` (`facility_id`,`start_time`,`end_time`,`status`),
  KEY `campus_bookings_user_id_11e7a67e_fk_campus_users_id` (`user_id`),
  KEY `campus_bookings_start_time_c7ece57c` (`start_time`),
  KEY `campus_bookings_end_time_ce1cf89c` (`end_time`),
  KEY `campus_bookings_status_b9f195ee` (`status`),
  CONSTRAINT `campus_bookings_facility_id_4f22104b_fk_campus_facilities_id` FOREIGN KEY (`facility_id`) REFERENCES `campus_facilities` (`id`),
  CONSTRAINT `campus_bookings_user_id_11e7a67e_fk_campus_users_id` FOREIGN KEY (`user_id`) REFERENCES `campus_users` (`id`),
  CONSTRAINT `booking_end_time_after_start_time` CHECK ((`end_time` > `start_time`))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_tickets
CREATE TABLE `campus_tickets` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `location_custom` varchar(150) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `assigned_to_id` bigint DEFAULT NULL,
  `created_by_id` bigint NOT NULL,
  `facility_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `campus_tickets_assigned_to_id_6584b3b8_fk_campus_users_id` (`assigned_to_id`),
  KEY `campus_tickets_created_by_id_c4449e02_fk_campus_users_id` (`created_by_id`),
  KEY `campus_tickets_facility_id_ee99797f_fk_campus_facilities_id` (`facility_id`),
  KEY `campus_tickets_priority_be8ced5a` (`priority`),
  KEY `campus_tickets_status_fff5f62d` (`status`),
  CONSTRAINT `campus_tickets_assigned_to_id_6584b3b8_fk_campus_users_id` FOREIGN KEY (`assigned_to_id`) REFERENCES `campus_users` (`id`),
  CONSTRAINT `campus_tickets_created_by_id_c4449e02_fk_campus_users_id` FOREIGN KEY (`created_by_id`) REFERENCES `campus_users` (`id`),
  CONSTRAINT `campus_tickets_facility_id_ee99797f_fk_campus_facilities_id` FOREIGN KEY (`facility_id`) REFERENCES `campus_facilities` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_comments
CREATE TABLE `campus_comments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `comment` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `author_id` bigint NOT NULL,
  `ticket_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `campus_comments_author_id_1e485c57_fk_campus_users_id` (`author_id`),
  KEY `campus_comments_ticket_id_1b7bc0c3_fk_campus_tickets_id` (`ticket_id`),
  CONSTRAINT `campus_comments_author_id_1e485c57_fk_campus_users_id` FOREIGN KEY (`author_id`) REFERENCES `campus_users` (`id`),
  CONSTRAINT `campus_comments_ticket_id_1b7bc0c3_fk_campus_tickets_id` FOREIGN KEY (`ticket_id`) REFERENCES `campus_tickets` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_sla_policies
CREATE TABLE `campus_sla_policies` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `response_time_hours` int unsigned NOT NULL,
  `resolution_time_hours` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `priority` (`priority`),
  CONSTRAINT `campus_sla_policies_chk_1` CHECK ((`response_time_hours` >= 0)),
  CONSTRAINT `campus_sla_policies_chk_2` CHECK ((`resolution_time_hours` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_sensor_events
CREATE TABLE `campus_sensor_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sensor_type` varchar(50) NOT NULL,
  `metric_value` decimal(10,2) NOT NULL,
  `unit` varchar(20) NOT NULL,
  `recorded_at` datetime(6) NOT NULL,
  `raw_payload` json NOT NULL,
  `facility_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_se_fac_typ_rec` (`facility_id`,`sensor_type`,`recorded_at`),
  KEY `campus_sensor_events_sensor_type_76025299` (`sensor_type`),
  KEY `campus_sensor_events_recorded_at_4ddbebba` (`recorded_at`),
  CONSTRAINT `campus_sensor_events_facility_id_dd6a98dc_fk_campus_fa` FOREIGN KEY (`facility_id`) REFERENCES `campus_facilities` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_approvals
CREATE TABLE `campus_approvals` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `status` varchar(20) NOT NULL,
  `remarks` longtext NOT NULL,
  `reviewed_at` datetime(6) NOT NULL,
  `reviewer_id` bigint NOT NULL,
  `booking_id` bigint DEFAULT NULL,
  `ticket_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `campus_approvals_reviewer_id_a4156822_fk_campus_users_id` (`reviewer_id`),
  KEY `campus_approvals_booking_id_a24b15f7_fk_campus_bookings_id` (`booking_id`),
  KEY `campus_approvals_ticket_id_c5efb0b2_fk_campus_tickets_id` (`ticket_id`),
  KEY `campus_approvals_status_b1c083c4` (`status`),
  CONSTRAINT `campus_approvals_booking_id_a24b15f7_fk_campus_bookings_id` FOREIGN KEY (`booking_id`) REFERENCES `campus_bookings` (`id`),
  CONSTRAINT `campus_approvals_reviewer_id_a4156822_fk_campus_users_id` FOREIGN KEY (`reviewer_id`) REFERENCES `campus_users` (`id`),
  CONSTRAINT `campus_approvals_ticket_id_c5efb0b2_fk_campus_tickets_id` FOREIGN KEY (`ticket_id`) REFERENCES `campus_tickets` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for campus_audit_events
CREATE TABLE `campus_audit_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(100) NOT NULL,
  `resource_type` varchar(50) NOT NULL,
  `resource_id` varchar(50) NOT NULL,
  `details` json NOT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `actor_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `campus_audit_events_actor_id_579d2aba_fk_campus_users_id` (`actor_id`),
  KEY `campus_audit_events_action_601d1b8d` (`action`),
  KEY `campus_audit_events_resource_type_eb8efb11` (`resource_type`),
  KEY `campus_audit_events_created_at_b07550d4` (`created_at`),
  CONSTRAINT `campus_audit_events_actor_id_579d2aba_fk_campus_users_id` FOREIGN KEY (`actor_id`) REFERENCES `campus_users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
