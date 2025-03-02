# Step 1: Specify the base image
FROM php:8.2-apache

# Step 2: Install any necessary PHP extensions
# For example, to install MySQL extension:
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Step 3: Copy application code into the container
COPY . /var/www/html/

# Step 4: Set permissions if necessary
RUN chown -R www-data:www-data /var/www/html

# Step 5: Expose port 80
EXPOSE 80

# Step 6: Start Apache server
CMD ["apache2-foreground"]
