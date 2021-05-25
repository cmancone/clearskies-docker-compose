CREATE TABLE `statuses` (
  `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `statuses` (`id`,`name`) VALUES (1,'Active');
INSERT INTO `statuses` (`id`,`name`) VALUES (2,'Disabled');
