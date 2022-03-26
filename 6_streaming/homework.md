## **Q1**: Which option allows Kafka to scale?

Partitions

## **Q2**: Which option provide fault tolerance to kafka?

Replication

## **Q3**: What is a compact topic?

Topic which compact messages based on Key

## **Q4**: Role of schemas in Kafka

* Making consumer producer independent of each other
* Provide possibility to update messages without breaking change

## **Q5**: Which configuration should a producer set to provide guarantee that a message is never lost?

`ack=all`

## **Q6**: From where all can a consumer start consuming messages from?

* Beginning in topic
* Latest in topic
* From a particular offset ( https://developer.confluent.io/tutorials/kafka-console-consumer-read-specific-offsets-partitions/confluent.html )

## **Q7**: What key structure is seen when producing messages via 10 minutes Tumbling window in Kafka stream?

[Key, Start Timestamp, Start Timestamp + 10 mins]

## **Q8**: Benefit of Global KTable?

Efficient joins

## **Q9**: When joining KTable with KTable partitions should be...

Same

## **Q10**: When joining KStream with Global KTable partitions should be...

Does not matter

## **Q11**: (Attach code link) Practical: Create two streams with same key and provide a solution where you are joining the two keys

(no code)