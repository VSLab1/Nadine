plugins {
    id("java")
    id("com.google.protobuf") version "0.9.4"
}
group = "org.example" //Achtung: Package-Name anpassen !
version = "1.0.0"
java.sourceCompatibility = JavaVersion.VERSION_11 //zuhause ggf. VERSION_17
repositories {
    mavenCentral()
}
dependencies { //Hinweis: zuhause ggf. neuere Versionen verwenden
    implementation("io.grpc:grpc-netty-shaded:1.71.0")
    implementation("io.grpc:grpc-protobuf:1.71.0")
    implementation("io.grpc:grpc-stub:1.71.0")
    implementation("javax.annotation:javax.annotation-api:1.3.2")
    testImplementation("junit:junit:4.13.2")
}
protobuf {
    protoc {
        artifact = "com.google.protobuf:protoc:3.25.1" //zuhause ggf. 4.32.1
    }
    plugins {
        create("grpc") {
            artifact = "io.grpc:protoc-gen-grpc-java:1.71.0" //ggf. anpassen
        }
    }
    generateProtoTasks {
        all().forEach { task ->
            task.plugins {
                create("grpc") {}
            }
        }
    }
}
tasks.named<ProcessResources>("processResources") {
    exclude("**/*.proto")
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
}
sourceSets {
    main {
        proto {
            srcDir("src/main/proto")
        }
    }
}