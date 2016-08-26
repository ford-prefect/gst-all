#!/usr/bin/env python3

import os
import argparse
import subprocess


SCRIPTDIR = os.path.dirname(__file__)


def prepend_env_var(env, var, value):
    env[var] = os.pathsep + value + os.pathsep + env.get(var, "")
    env[var] = env[var].replace(os.pathsep + os.pathsep, os.pathsep).strip(os.pathsep)

def set_prompt_var(options, env):
    ps1 = env.get("PS1")
    if ps1:
        env["PS1"] = "[gst-%s] %s" % (options.gst_version, ps1)

    prompt = env.get("PROMPT")
    if prompt:
        env["PROMPT"] = "[gst-%s] %s" % (options.gst_version, prompt)


def get_subprocess_env(options):
    env = os.environ.copy()

    PATH = env.get("PATH", "")
    subprojects_path = os.path.join(options.builddir, "subprojects")
    for proj in os.listdir(subprojects_path):
        projpath = os.path.join(subprojects_path, proj)
        if not os.path.exists(projpath):
            print("Subproject %s does not exist in %s.,\n"
                  " Make sure to build everything properly "
                  "and try again." % (proj, projpath))
            exit(1)

        envvars_file = os.path.join(projpath, os.path.basename(projpath) + "-uninstalled-envvars.py")
        if os.path.exists(envvars_file):
            envvars_env = {"envvars": {}}
            with open(envvars_file) as f:
                code = compile(f.read(), envvars_file, 'exec')
                exec(code, None, envvars_env)
            for var, value in envvars_env["envvars"].items():
                if var.startswith("+"):
                    prepend_env_var(env, var, value.strip("+"))
                else:
                    env[var] = value

        toolsdir = os.path.join(projpath, "tools")
        if os.path.exists(toolsdir):
            prepend_env_var(env, "PATH", toolsdir)

        prepend_env_var(env, "GST_PLUGIN_PATH", projpath)

    env["GST_VALIDATE_SCENARIOS_PATH"] = os.path.normpath(
        "%s/subprojects/gst-devtools/validate/data/scenarios" % SCRIPTDIR)
    env["GST_VALIDATE_PLUGIN_PATH"] = os.path.normpath(
        "%s/subprojects/gst-devtools/validate/plugins" % options.builddir)
    prepend_env_var(env, "PATH", os.path.normpath(
        "%s/subprojects/gst-devtools/validate/tools" % options.builddir))
    env["PATH"] += os.pathsep + PATH
    env["GST_VERSION"] = options.gst_version
    env["GST_PLUGIN_SYSTEM_PATH"] = ""
    env["GST_PLUGIN_SCANNER"] = os.path.normpath(
        "%s/subprojects/gstreamer/libs/gst/helpers/gst-plugin-scanner" % options.builddir)
    env["GST_PTP_HELPER"] = os.path.normpath(
        "%s/subprojects/gstreamer/libs/gst/helpers/gst-ptp-helper" % options.builddir)
    env["GST_REGISTRY"] = os.path.normpath(options.builddir + "/registry.dat")

    set_prompt_var(options, env)

    return env


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="gstreamer-uninstalled")

    parser.add_argument("--builddir",
                        default=os.path.join(SCRIPTDIR, "build"),
                        help="The meson build directory")
    parser.add_argument("--gst-version", default="master",
                        help="The GStreamer major version")
    options = parser.parse_args()

    if not os.path.exists(options.builddir):
        print("GStreamer not built in %s\n\nBuild it and try again" %
              options.builddir)
        exit(1)

    shell_args = [os.environ.get("SHELL", os.path.realpath("/bin/sh"))]
    if shell_args[0] == "/bin/bash":
        shell_args.append("--noprofile")

    try:
        exit(subprocess.run(shell_args, env=get_subprocess_env(options)).returncode)
    except subprocess.CalledProcessError as e:
        exit(e.returncode)
