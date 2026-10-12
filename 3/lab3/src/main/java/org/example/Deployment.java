package org.example;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class Deployment {
    private static final ObjectMapper mapper = new ObjectMapper();

    public static void main(String[] args) {
        String jsonPath = "mynet.json";
        if (args.length > 0) {
            jsonPath = args[0];
        }

        try {
            File jsonFile = new File(jsonPath);
            if (!jsonFile.exists()) {
                System.err.println("JSON-file not found under: " + jsonFile.getAbsolutePath());
                return;
            }

            List<NodeConfig> configs = mapper.readValue(jsonFile, new TypeReference<List<NodeConfig>>() {});
            System.out.println("Deployment: " + configs.size() + " Node-configuration loaded.");

            if (configs.size() < 10) {
                System.err.println("Network has to have at least 10 nodes. Please add more nodes to the JSON-file.");
                System.err.println("current number of nodes JSON-File: " + configs.size());
                return;
            }

            List<Process> startedProcesses = new ArrayList<>();

            String jarPath = Deployment.class.getProtectionDomain().getCodeSource().getLocation().getPath();
            boolean isJar = jarPath.endsWith(".jar");

            // 1. start CONTROLLER in new window
            List<String> controllerCmd = new ArrayList<>();
            String os = System.getProperty("os.name").toLowerCase();

            if (os.contains("win")) {
                if (isJar) {
                    // Wenn es eine JAR ist, starten wir den Controller direkt aus der JAR
                    controllerCmd.addAll(List.of("cmd", "/c", "start", "cmd", "/k", "java", "-cp", jarPath, "org.example.Controller"));
                } else {
                    String classpath = System.getProperty("java.class.path");
                    controllerCmd.addAll(List.of("cmd", "/c", "start", "cmd", "/k", "java", "-cp", classpath, "org.example.Controller"));
                }
            } else {
                // Linux/Mac
                if (isJar) {
                    controllerCmd.addAll(List.of("x-terminal-emulator", "-e", "java", "-cp", jarPath, "org.example.Controller"));
                } else {
                    String classpath = System.getProperty("java.class.path");
                    controllerCmd.addAll(List.of("x-terminal-emulator", "-e", "java", "-cp", classpath, "org.example.Controller"));
                }
            }

            ProcessBuilder controllerPb = new ProcessBuilder(controllerCmd);
            Process controllerProcess = controllerPb.start();
            startedProcesses.add(controllerProcess);
            System.out.println("Controller was started in new seperate window.");

            // wait for controller to be ready
            Thread.sleep(1000);

            // 2. start all nodes
            for (NodeConfig config : configs) {
                List<String> command = new ArrayList<>();
//                command.add("ssh");
//                command.add("-o");
//                command.add("BatchMode=yes");
//                command.add("student@127.0.0.1");
////                command.add("home/student/IdeaProjects/.../scripts/startnode");

                command.add("java");
                command.add("-Dfile.encoding=UTF-8");
                command.add("-cp");
                command.add(isJar ? jarPath : System.getProperty("java.class.path"));
                command.add("org.example.Main");

                command.add(config.address);
                command.add(config.controllerAddress);
                command.add(String.valueOf(config.storage));

                if (config.neighbors != null) {
                    command.addAll(config.neighbors);
                }

                ProcessBuilder pb = new ProcessBuilder(command);
                pb.inheritIO();

                Process process = pb.start();
                startedProcesses.add(process);
                System.out.println("process started for Node: " + config.address);
            }

            System.out.println("System is running. if window is closed all processes are terminated.");

            // Shutdown-Hook for cleanup
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("\nDeployment ended. stop all processes...");
                for (Process p : startedProcesses) {
                    p.destroy();
                }
            }));

            while (startedProcesses.stream().anyMatch(Process::isAlive)) {
                Thread.sleep(1000);
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("error on Deployment: " + e.getMessage());
        }
    }

    public static class NodeConfig {
        public String address;
        public int storage;
        public String controllerAddress;
        public List<String> neighbors;
    }
}