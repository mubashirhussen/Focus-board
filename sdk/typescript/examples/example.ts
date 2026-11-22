import { FocusBoardClient } from '../src';

async function main() {
  const client = new FocusBoardClient({
    apiKey: 'fb_live_sample_key_12345',
  });

  console.log('Fetching tasks via TypeScript SDK...');
  try {
    const tasks = await client.listTasks({ limit: 5 });
    console.log(`Found ${tasks.length} tasks.`);

    const newTask = await client.createTask({
      title: 'Automated SDK Integration Test',
      priority: 'high',
      category: 'Engineering',
    });
    console.log(`Created task with ID: ${newTask.id}`);
  } catch (error) {
    console.error('Error in TypeScript client:', error);
  }
}

main();
