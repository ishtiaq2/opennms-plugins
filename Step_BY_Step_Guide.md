# OpenNMS Horizon 33.1.8
# PostgreSQL: Version 14.

# Install Prerequisites:
    # Java 17: Depending on your Horizon version (Horizon 33+ uses 17).
        sudo yum install java-17-openjdk-devel.x86_64 -y 

    # Maven: The build tool used for OpenNMS.
        cd /opt
        sudo wget https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz
        sudo tar -xvf apache-maven-3.9.9-bin.tar.gz
        # Create the symlink
        sudo ln -s /opt/apache-maven-3.9.9 /opt/maven
        
    # Create the Environment Script
        sudo tee /etc/profile.d/opennms_dev.sh <<EOF
        # Java 17 Path
        export JAVA_HOME=/usr/lib/jvm/java-17-openjdk

        # Maven Path (pointing to the directory you just created)
        export MAVEN_HOME=/opt/apache-maven-3.9.9

        # Add both to the system PATH
        export PATH=\$JAVA_HOME/bin:\$MAVEN_HOME/bin:\$PATH
        EOF

    # Set the Permissions
    sudo chmod +x /etc/profile.d/opennms_dev.sh

    # Activate and Verify
    source /etc/profile.d/opennms_dev.sh
    java -version
    mvn -version

    Node.js & npm: Required for the Vue.js frontend part.
    


# Understand the Architecture:
    Backend (Java): Registers the plugin with OpenNMS and provides data via APIs.
    Frontend (Vue.js): The actual user interface that appears in the OpenNMS web console.
