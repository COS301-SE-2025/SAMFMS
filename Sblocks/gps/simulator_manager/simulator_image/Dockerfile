FROM openjdk:17-jdk
WORKDIR /simulator
COPY tracker-server.jar .
ENTRYPOINT ["java", "-cp", "tracker-server.jar", "org.traccar.simulator.Main"]