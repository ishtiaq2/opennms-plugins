package org.example.opennms.lab.nodeinventory;

import org.opennms.integration.api.v1.ui.UIExtension;

/**
 * Registered as an OSGi service in OSGI-INF/blueprint/blueprint.xml.
 *
 * <p>OpenNMS core tracks every {@link UIExtension} service (UIExtensionRegistryImpl) and
 * serves the module file through UIExtensionServiceImpl, which calls
 * {@code FrameworkUtil.getBundle(getExtensionClass()).getResource(path)}.
 * That is why {@link #getExtensionClass()} must return a class that lives in
 * <em>this</em> bundle: the class is how OpenNMS finds the JAR that contains the JS.</p>
 *
 * <p>Note what this bundle does <em>not</em> contain: images. The REST endpoint only
 * serves the module (as application/javascript) and {resourceRoot}/style.css (as
 * text/css), so shared images are fetched from /opennms/assets/shared/ instead.</p>
 */
public class NodeInventoryUIExtension implements UIExtension {

    private String extensionId;
    private String menuEntry;
    private String resourceRootPath;
    private String moduleFileName;

    @Override
    public String getExtensionId() {
        return extensionId;
    }

    @Override
    public String getMenuEntry() {
        return menuEntry;
    }

    @Override
    public String getResourceRootPath() {
        return resourceRootPath;
    }

    @Override
    public String getModuleFileName() {
        return moduleFileName;
    }

    @Override
    public Class<? extends UIExtension> getExtensionClass() {
        return getClass();
    }

    public void setExtensionId(final String extensionId) {
        this.extensionId = extensionId;
    }

    public void setMenuEntry(final String menuEntry) {
        this.menuEntry = menuEntry;
    }

    public void setResourceRootPath(final String resourceRootPath) {
        this.resourceRootPath = resourceRootPath;
    }

    public void setModuleFileName(final String moduleFileName) {
        this.moduleFileName = moduleFileName;
    }
}
