# Generating the Project Template
    OpenNMS provides a "Maven Archetype" (a project blueprint) so you don't have to write the boilerplate code from scratch.

    Run the Generator:
    Open your terminal and run this command:
    (This creates a folder named my-ui-extension with a pre-configured structure: plugin (code), karaf-features 
    (deployment info), and assembly (packaging).)
    
    mvn archetype:generate -B \
    -DarchetypeGroupId=org.opennms.integration.api \
    -DarchetypeArtifactId=example-kar-plugin \
    -DarchetypeVersion=1.0.0 \
    -DgroupId=com.mycompany.opennms \
    -DartifactId=my-ui-extension \
    -Dversion=1.0.0-SNAPSHOT \
    -Dpackage=com.mycompany.opennms.plugin \
    -DpluginId=my-ui-extension \
    -DpluginName="My First UI Extension"

# Step 2: Register the Service (The OSGi Step)
    <bean id="myUiExtensionBean" class="com.mycompany.MyFirstUiExtension" />
    <service ref="myUiExtensionBean" interface="org.opennms.integration.api.v1.ui.UiExtension" />

# Step 3: Create the Frontend "Landing Page"
    The getUrl() in Step 1 points to /extensions/my-ui-lab/index.html. You need to create this file so there is actually something to display.
    Create the folder: plugin/src/main/resources/webapp/
    Create index.html inside it:
    ```html
    <!DOCTYPE html>
    <html>
    <head>
        <title>My First UI Extension</title>
    </head>
    <body>
        <h1>Hello World!</h1>
    </body>
    </html>

# step 3.5: Add the OpenNMS Repository
    Open your root pom.xml (the one located at /tmp/opennms-lab/opennms-lab/plugins/my-ui-extension/pom.xml) and 
    ensure the following <repositories> block is present. If it’s not there, add it right before the <build> or 
    <dependencies> section:

    <repositories>
        <repository>
            <id>opennms-repo</id>
            <name>OpenNMS Repository</name>
            <url>https://repo.opennms.org/maven2/</url>
            <releases>
                <enabled>true</enabled>
            </releases>
            <snapshots>
                <enabled>true</enabled>
            </snapshots>
        </repository>
    </repositories>

# step 3.6: Fix the Dependency Name
    There is a high chance that org.opennms.integration.api:ui is actually part of the main api artifact in the 
    version you are using. In your plugin/pom.xml, try changing the artifact ID from ui to api:

    <dependency>
        <groupId>org.opennms.integration.api</groupId>
        <artifactId>api</artifactId> 
        <version>${opennms.api.version}</version>
        <scope>provided</scope>
    </dependency>

# Step 4: Update the Build Configuration
    Open your pom.xml in the plugin folder and ensure you have the opennms-integration-api dependency. 
    It should already be there, but verify it includes the ui packages:
    <dependency>
        <groupId>org.opennms.integration.api</groupId>
        <artifactId>api</artifactId>
        <version>${opennms.api.version}</version>
        <scope>provided</scope>
    </dependency>
 
# Step 5: Update the Build Instructions
    OpenNMS needs to know that your bundle contains web assets (HTML/CSS). In your plugin/pom.xml, find the 
    <instructions> block and add the <Include-Resource> tag:    
    <configuration>
        <instructions>
            <Karaf-Commands>*</Karaf-Commands>
            <Include-Resource>
                {maven-resources},
                webapp=src/main/resources/webapp
            </Include-Resource>
            <Export-Package></Export-Package>
        </instructions>
    </configuration>    

# Step 6: Build and Deploy the Bundle🚀 The Final Milestone: Build & Run
    Since your code and configuration are ready, it's time to see the fruits of your labor.

    Compile and Package:
    From your project root, run:
    
    Bash
    mvn clean install
    # rm -rf ~/.m2/repository/org/opennms/integration
    # mvn clean install -U
    This creates the .jar for the plugin and the .kar (Karaf Archive) for deployment.
    
    Deploy to your Lab:
    Find the generated file in assembly/target/my-ui-extension-1.0.0-SNAPSHOT.kar and copy it to your OpenNMS deployment folder:
    
    Bash
    cp assembly/target/*.kar /opt/opennms/deploy/
    Verify the Activation:
    Log into the OpenNMS Karaf shell (usually ssh -p 8101 admin@localhost) and run:
    
    Bash
    bundle:list | grep -i "My First UI Extension"
    If it says Active, your plugin is live!
