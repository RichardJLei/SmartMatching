# Async Action Management Best Practices

## Sync Management Strategy (Refine-native Approach)

### 1. State Management Hierarchy
1. **Server State** (Primary source)
   - Managed automatically through data providers
   - Accessed via:
   ```typescript
   useCustom(), useList(), useOne()
   ```
2. **Client State** (Derived state)
   - Managed through React Query cache
   - Automatic updates via query invalidation


### 2. Implementation Pattern
typescript
// Start long-running task
const { mutate: startTask } = useCustom();
// Check task status (auto-polling)
const { data: taskStatus } = useCustom({
queryOptions: {
enabled: !!taskId,
refetchInterval: 1000
}
});
// Handle completion
const invalidate = useInvalidate();
const { open } = useNotification();
useEffect(() => {
if (taskStatus?.data?.status === "completed") {
invalidate(["blogPosts"]);
open({ type: "success", message: "Task completed" });
}
}, [taskStatus]);



### 3. Status Synchronization
| Mechanism          | Implementation                          | Benefit                          |
|--------------------|-----------------------------------------|----------------------------------|
| Auto-polling       | `refetchInterval` in useCustom          | Zero-config updates              |
| Cache Invalidation | `useInvalidate()` post-completion       | Consistent data views            |
| WebSocket Support  | `liveProvider` integration              | Real-time updates                |
| Mutation Hooks     | `onSuccess/onError` callbacks            | Coordinated UI updates           |

### 4. Compliance Checklist
- [ ] Use only data provider methods for state mutations
- [ ] Leverage React Query's staleTime/cacheTime
- [ ] Utilize unified error handling via notifications
- [ ] Implement auto-retry through query config
- [ ] Avoid useState for server-state mirroring

