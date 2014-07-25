import source_base
import os
import shutil

class SourceArchive(source_base.SourceBase):
    def __init__(self):
        source_base.SourceBase.__init__(self)

    def install(self, scheme, path, toolName, toolbox, version=None, build=None):
        """Installs tool from the path specified.
        Returns True if tool was installed successfully"""
        if path.endswith(".tar") or path.endswith("tar.gz"):
            return SourceArchive.installTar(path, toolName, toolbox)
        elif path.endswith(".zip"):
            return SourceArchive.installZip(path, toolName, toolbox)
        else:
            print "Unsupported archive format", path
            return False

    @staticmethod
    def installZip(path, toolName, toolbox):
        import zipfile
        zip = zipfile.ZipFile(path)
        if not os.path.isfile(path):
            print "File %s doesn't exist or is not a file" % path
            return False
        def files(aZip):
            filtered = []
            for f in aZip.namelist():
                pathComponents = f.split("/")
                if (".." not in pathComponents) and (pathComponents[0] == toolName):
                   filtered.append(f)
            return filtered
        succeeded = False
        try:
            zip = zipfile.ZipFile(path, "r")
            zip.extractall(path=toolbox.getToolsPath(), members=files(zip))
            somethingWasInstalled = os.path.isdir(toolbox.getToolPath(toolName))
            if not somethingWasInstalled:
                print "Nothing was extracted to tool folder"
            succeeded = somethingWasInstalled
            zip.close()
        except zipfile.BadZipfile as bzf:
            print "tar file extraction error occured: %s" % str(bzf)
            return False
        except IOError as ioerror:
            print str(ioerror)
            return False
        except OSError as oserror:
            print str(oserror)
            return False
        finally:
            if not succeeded:
                try:
                    shutil.rmtree(toolbox.getToolPath(toolName), ignore_errors=True)
                except:
                    pass
        return True
    
    @staticmethod
    def installTar(path, toolName, toolbox):
        import tarfile
        def files(members):
            for tarinfo in members:
                pathComponents = tarinfo.name.split("/")
                if (".." not in pathComponents) and (pathComponents[0] == toolName):
                    yield tarinfo

        if not os.path.isfile(path):
            print "File %s doesn't exist or is not a file" % path
            return False
        succeeded = False
        try:
            tar = tarfile.open(path)
            tar.extractall(path=toolbox.getToolsPath(), members=files(tar))
            somethingWasInstalled = os.path.isdir(toolbox.getToolPath(toolName))
            if not somethingWasInstalled:
                print "Nothing was extracted to tool folder"
            succeeded = somethingWasInstalled
            tar.close()
        except tarfile.TarError as te:
            print "tar file extraction error occured: %s" % str(te)
            return False
        except IOError as ioerror:
            print str(ioerror)
            return False
        except OSError as oserror:
            print str(oserror)
            return False
        finally:
            if not succeeded:
                try:
                    shutil.rmtree(toolbox.getToolPath(toolName), ignore_errors=True)
                except:
                    pass
        return True
        